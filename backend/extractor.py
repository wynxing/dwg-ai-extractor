from __future__ import annotations

import json
import re
from typing import Any

from .context_builder import build_llm_context
from .llm_client import ChatMessage, OpenAICompatibleClient
from .models import DrawingContext, ExtractionTemplate, LLMConfig


class ExtractionError(RuntimeError):
    pass


SYSTEM_PROMPT = """你是机械图纸和工程文档的信息抽取器。
只能依据用户提供的 CAD 文字上下文抽取字段，不得编造。
如果字段无法确定，返回空字符串。
必须只输出一个 JSON object，不要输出 Markdown、解释或多余文本。
"""


def extract_fields_with_llm(
    context: DrawingContext,
    template: ExtractionTemplate,
    llm_config: LLMConfig,
    sequence: int,
    client: OpenAICompatibleClient | None = None,
) -> dict[str, str]:
    client = client or OpenAICompatibleClient(llm_config)
    prompt = build_user_prompt(context, template, sequence)
    content = client.chat([ChatMessage("system", SYSTEM_PROMPT), ChatMessage("user", prompt)])
    raw = parse_json_object(content)
    values = normalize_result(raw, template, sequence)
    validate_required(values, template)
    return values


def build_user_prompt(context: DrawingContext, template: ExtractionTemplate, sequence: int) -> str:
    llm_context = build_llm_context(context)
    fields = [
        {
            "key": field.key,
            "label": field.label,
            "description": field.description,
            "required": field.required,
            "example": field.example,
        }
        for field in template.fields
    ]
    schema = {field.key: field.example or "" for field in template.fields}
    payload = {
        "task": "Extract one row of structured fields from CAD text records.",
        "sequence": sequence,
        "fields": fields,
        "output_json_keys": schema,
        "rules": [
            "Only use the provided file name and text_records.",
            "Return empty string for unknown fields.",
            "Do not include binary file contents or image assumptions.",
            "For image fields, return empty string unless text explicitly provides an image value.",
        ],
        "cad_context": llm_context,
        "example_output": schema,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def parse_json_object(content: str) -> dict[str, Any]:
    text = content.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start < 0 or end <= start:
            raise ExtractionError("模型输出不是 JSON object")
        data = json.loads(text[start : end + 1])
    if not isinstance(data, dict):
        raise ExtractionError("模型输出 JSON 不是 object")
    return data


def normalize_result(data: dict[str, Any], template: ExtractionTemplate, sequence: int) -> dict[str, str]:
    values: dict[str, str] = {}
    for field in template.fields:
        raw = data.get(field.key, "")
        if raw is None:
            value = ""
        elif isinstance(raw, (dict, list)):
            value = json.dumps(raw, ensure_ascii=False)
        else:
            value = str(raw)

        if field.postprocess == "sequence":
            value = str(sequence)
        elif field.postprocess == "force_empty":
            value = ""
        elif field.postprocess == "empty_if_unknown" and value.strip() in {"未知", "不确定", "N/A", "NA", "null", "None"}:
            value = ""
        else:
            value = value.strip()
        values[field.key] = value
    return values


def validate_required(values: dict[str, str], template: ExtractionTemplate) -> None:
    missing = [field.label for field in template.fields if field.required and not values.get(field.key, "").strip()]
    if missing:
        raise ExtractionError(f"必填字段缺失：{', '.join(missing)}")
