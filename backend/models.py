from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class FieldSpec:
    key: str
    label: str
    description: str = ""
    required: bool = False
    example: str = ""
    postprocess: str = "strip"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FieldSpec":
        return cls(
            key=str(data["key"]),
            label=str(data["label"]),
            description=str(data.get("description", "")),
            required=bool(data.get("required", False)),
            example=str(data.get("example", "")),
            postprocess=str(data.get("postprocess", "strip")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "label": self.label,
            "description": self.description,
            "required": self.required,
            "example": self.example,
            "postprocess": self.postprocess,
        }


@dataclass(slots=True)
class ExtractionTemplate:
    template_id: str
    name: str
    fields: list[FieldSpec]
    output_sheet_name: str = "提取结果"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExtractionTemplate":
        return cls(
            template_id=str(data["template_id"]),
            name=str(data["name"]),
            output_sheet_name=str(data.get("output_sheet_name", "提取结果")),
            fields=[FieldSpec.from_dict(item) for item in data.get("fields", [])],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "template_id": self.template_id,
            "name": self.name,
            "output_sheet_name": self.output_sheet_name,
            "fields": [field.to_dict() for field in self.fields],
        }


@dataclass(slots=True)
class LLMConfig:
    base_url: str = "https://api.openai.com/v1"
    api_key_env_var: str = "OPENAI_API_KEY"
    model: str = ""
    temperature: float = 0.0
    timeout_seconds: int = 60
    max_retries: int = 2
    use_json_object: bool = True
    extra_headers: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LLMConfig":
        return cls(
            base_url=str(data.get("base_url", "https://api.openai.com/v1")),
            api_key_env_var=str(data.get("api_key_env_var", "OPENAI_API_KEY")),
            model=str(data.get("model", "")),
            temperature=float(data.get("temperature", 0)),
            timeout_seconds=int(data.get("timeout_seconds", 60)),
            max_retries=int(data.get("max_retries", 2)),
            use_json_object=bool(data.get("use_json_object", True)),
            extra_headers={str(key): str(value) for key, value in dict(data.get("extra_headers", {})).items()},
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "base_url": self.base_url,
            "api_key_env_var": self.api_key_env_var,
            "model": self.model,
            "temperature": self.temperature,
            "timeout_seconds": self.timeout_seconds,
            "max_retries": self.max_retries,
            "use_json_object": self.use_json_object,
            "extra_headers": self.extra_headers,
        }


@dataclass(slots=True)
class ConverterConfig:
    executable_path: str = ""
    output_version: str = "ACAD2018"
    audit: bool = True


@dataclass(slots=True)
class AppConfig:
    converter: ConverterConfig = field(default_factory=ConverterConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    template_path: str = ""
    output_dir: str = ""
    recursive: bool = True


@dataclass(slots=True)
class TextRecord:
    text: str
    source_space: str
    layer: str = ""
    block_name: str = ""
    entity_type: str = ""
    x: float | None = None
    y: float | None = None
    z: float | None = None

    def to_context_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "source_space": self.source_space,
            "block_name": self.block_name,
            "entity_type": self.entity_type,
            "layer": self.layer,
            "x": self.x,
            "y": self.y,
        }


@dataclass(slots=True)
class DrawingContext:
    file_path: Path
    records: list[TextRecord]


@dataclass(slots=True)
class ExtractionResult:
    file_path: Path
    status: str
    values: dict[str, str] = field(default_factory=dict)
    error: str = ""
    elapsed_seconds: float = 0.0


@dataclass(slots=True)
class BatchJob:
    input_paths: list[Path]
    output_excel_path: Path
    template: ExtractionTemplate
    llm: LLMConfig
    converter: ConverterConfig = field(default_factory=ConverterConfig)
    recursive: bool = True
