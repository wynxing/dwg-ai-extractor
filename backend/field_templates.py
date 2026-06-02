from __future__ import annotations

import json
from pathlib import Path

from .models import ExtractionTemplate, FieldSpec

SUPPORTED_POSTPROCESSORS = {"strip", "empty_if_unknown", "force_empty", "sequence"}


DEFAULT_TEMPLATE = ExtractionTemplate(
    template_id="default_bom_v1",
    name="默认物料明细模板",
    output_sheet_name="物料明细表",
    fields=[
        FieldSpec("sequence", "序号", "输出行序号。由程序生成，模型可留空。", True, "1", "sequence"),
        FieldSpec("item_code", "物料编码", "物料编码或图纸编号，例如 M930102593。", True, "M930102593", "strip"),
        FieldSpec("item_name", "物料名称", "零件名称或物料名称。", True, "指示镜片", "strip"),
        FieldSpec("image", "图片", "首版固定为空字符串。", False, "", "force_empty"),
        FieldSpec("material", "材料", "材料信息，颜色应放入颜色字段。", False, "PC，透光均匀，阻燃等级V-2", "strip"),
        FieldSpec("color", "颜色", "颜色或色板信息。", False, "乳白色（参考样板）", "strip"),
        FieldSpec("surface_treatment", "表面处理", "表面处理工艺。", False, "局部抛光", "strip"),
    ],
)


def load_template(path: Path | None = None) -> ExtractionTemplate:
    if path is None:
        validate_template(DEFAULT_TEMPLATE)
        return DEFAULT_TEMPLATE
    with path.open("r", encoding="utf-8") as file:
        template = ExtractionTemplate.from_dict(json.load(file))
    validate_template(template)
    return template


def save_template(template: ExtractionTemplate, path: Path) -> None:
    validate_template(template)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(template.to_dict(), file, ensure_ascii=False, indent=2)


def validate_template(template: ExtractionTemplate) -> None:
    if not template.fields:
        raise ValueError("字段模板至少需要一个字段")
    ensure_required_field_values(template)
    ensure_unique_field_keys(template)
    ensure_supported_postprocessors(template)


def ensure_required_field_values(template: ExtractionTemplate) -> None:
    missing_keys = [field.label or f"第 {index} 行" for index, field in enumerate(template.fields, start=1) if not field.key.strip()]
    if missing_keys:
        raise ValueError(f"字段 key 不能为空：{', '.join(missing_keys)}")
    missing_labels = [field.key for field in template.fields if not field.label.strip()]
    if missing_labels:
        raise ValueError(f"字段表头不能为空：{', '.join(missing_labels)}")


def ensure_unique_field_keys(template: ExtractionTemplate) -> None:
    keys = [field.key for field in template.fields]
    duplicated = sorted({key for key in keys if keys.count(key) > 1})
    if duplicated:
        raise ValueError(f"字段 key 重复：{', '.join(duplicated)}")


def ensure_supported_postprocessors(template: ExtractionTemplate) -> None:
    invalid = sorted({field.postprocess for field in template.fields if field.postprocess not in SUPPORTED_POSTPROCESSORS})
    if invalid:
        raise ValueError(f"不支持的后处理：{', '.join(invalid)}")
