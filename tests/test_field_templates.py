from pathlib import Path

from backend.field_templates import DEFAULT_TEMPLATE, ensure_unique_field_keys, load_template, save_template, validate_template
from backend.models import ExtractionTemplate, FieldSpec


def test_default_template_column_order_is_stable() -> None:
    assert [field.label for field in DEFAULT_TEMPLATE.fields] == ["序号", "物料编码", "物料名称", "图片", "材料", "颜色", "表面处理"]
    assert [field.key for field in DEFAULT_TEMPLATE.fields] == [
        "sequence",
        "item_code",
        "item_name",
        "image",
        "material",
        "color",
        "surface_treatment",
    ]


def test_template_roundtrip(tmp_path: Path) -> None:
    template = ExtractionTemplate("custom", "自定义", [FieldSpec("foo", "字段", required=True)], "结果")
    path = tmp_path / "template.json"

    save_template(template, path)
    loaded = load_template(path)

    assert loaded.template_id == "custom"
    assert loaded.fields[0].key == "foo"
    assert loaded.fields[0].required is True


def test_duplicate_field_keys_are_rejected() -> None:
    template = ExtractionTemplate("bad", "bad", [FieldSpec("a", "A"), FieldSpec("a", "B")])

    try:
        ensure_unique_field_keys(template)
    except ValueError as exc:
        assert "字段 key 重复" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_template_validation_rejects_empty_key() -> None:
    template = ExtractionTemplate("bad", "bad", [FieldSpec("", "字段")])

    try:
        validate_template(template)
    except ValueError as exc:
        assert "字段 key 不能为空" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_template_validation_rejects_unsupported_postprocess() -> None:
    template = ExtractionTemplate("bad", "bad", [FieldSpec("foo", "字段", postprocess="unknown")])

    try:
        validate_template(template)
    except ValueError as exc:
        assert "不支持的后处理" in str(exc)
    else:
        raise AssertionError("expected ValueError")
