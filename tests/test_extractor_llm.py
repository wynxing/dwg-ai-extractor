import json
from pathlib import Path

from backend.extractor import extract_fields_with_llm, normalize_result, parse_json_object, validate_required
from backend.field_templates import DEFAULT_TEMPLATE
from backend.llm_client import ChatMessage
from backend.models import DrawingContext, LLMConfig, TextRecord


class FakeClient:
    def __init__(self, content: str) -> None:
        self.content = content
        self.messages: list[ChatMessage] = []

    def chat(self, messages: list[ChatMessage]) -> str:
        self.messages = messages
        return self.content


def test_parse_json_object_accepts_markdown_fenced_json() -> None:
    assert parse_json_object('```json\n{"a": "b"}\n```') == {"a": "b"}


def test_extract_fields_with_llm_fills_sequence_and_forces_empty_image() -> None:
    content = json.dumps(
        {
            "item_code": "M930102593",
            "item_name": "指示镜片",
            "image": "should be removed",
            "material": "PC",
            "color": "乳白色",
            "surface_treatment": "局部抛光",
        },
        ensure_ascii=False,
    )
    context = DrawingContext(Path("M930102593_V1.0_指示镜片.dxf"), [TextRecord("材料 PC", "Model")])

    values = extract_fields_with_llm(context, DEFAULT_TEMPLATE, LLMConfig(model="fake"), 3, client=FakeClient(content))

    assert values["sequence"] == "3"
    assert values["image"] == ""
    assert values["item_code"] == "M930102593"


def test_required_field_validation_fails_when_missing() -> None:
    values = normalize_result({}, DEFAULT_TEMPLATE, 1)

    try:
        validate_required(values, DEFAULT_TEMPLATE)
    except Exception as exc:
        assert "必填字段缺失" in str(exc)
    else:
        raise AssertionError("expected validation failure")
