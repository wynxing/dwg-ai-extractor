from __future__ import annotations

from .models import DrawingContext, TextRecord


PRIORITY_KEYWORDS = (
    "标题栏",
    "title",
    "物料",
    "编码",
    "图号",
    "图纸",
    "零件",
    "名称",
    "材料",
    "颜色",
    "色板",
    "表面",
    "处理",
    "技术要求",
    "要求",
    "备注",
)

PRIORITY_BLOCK_HINTS = ("title", "标题", "bom", "明细", "物料")


def build_llm_context(
    context: DrawingContext,
    max_records: int = 500,
    max_text_chars: int = 24000,
    include_file_path_hint: bool = False,
) -> dict:
    records = []
    used_chars = 0
    for record in prioritize_records(context.records):
        text = normalize_cad_text(record.text)
        if not text:
            continue
        if len(records) >= max_records or used_chars >= max_text_chars:
            break
        remaining = max_text_chars - used_chars
        clipped_text = text[:remaining]
        used_chars += len(clipped_text)
        item = record.to_context_dict()
        item["text"] = clipped_text
        records.append(item)

    payload = {
        "file_name": context.file_path.name,
        "text_records": records,
        "record_count": len(records),
        "privacy_note": "Only extracted CAD text and metadata are included. DWG/DXF binaries and images are not sent.",
    }
    if include_file_path_hint:
        payload["file_path_hint"] = str(context.file_path)
    return payload


def prioritize_records(records: list[TextRecord]) -> list[TextRecord]:
    indexed_records = list(enumerate(records))
    indexed_records.sort(key=lambda item: (_record_priority(item[1]), item[0]))
    return [record for _, record in indexed_records]


def normalize_cad_text(text: str) -> str:
    return " ".join(text.replace("\u3000", " ").replace("\r", " ").replace("\n", " ").split()).strip()


def _record_priority(record: TextRecord) -> tuple[int, float, float]:
    searchable = " ".join([record.text, record.source_space, record.layer, record.block_name, record.entity_type]).lower()
    keyword_score = sum(1 for keyword in PRIORITY_KEYWORDS if keyword.lower() in searchable)
    block_bonus = 2 if any(hint in record.block_name.lower() for hint in PRIORITY_BLOCK_HINTS) else 0
    entity_bonus = 1 if record.entity_type in {"ATTRIB", "ATTDEF"} else 0
    y_rank = -(record.y or 0.0)
    x_rank = record.x or 0.0
    return (-(keyword_score + block_bonus + entity_bonus), y_rank, x_rank)
