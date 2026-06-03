from __future__ import annotations

import json
import os
import platform
from pathlib import Path
from typing import Any

from .models import AppConfig, ConverterConfig, LLMConfig


APP_DIR_NAME = "DWGAIExtractor"


def default_config_path() -> Path:
    system = platform.system()
    if system == "Windows":
        base = os.environ.get("APPDATA")
        if base:
            return Path(base) / APP_DIR_NAME / "config.json"
    elif system == "Darwin":
        return Path.home() / "Library" / "Application Support" / APP_DIR_NAME / "config.json"
    else:
        xdg = os.environ.get("XDG_CONFIG_HOME")
        base = Path(xdg) if xdg else Path.home() / ".config"
        return base / APP_DIR_NAME / "config.json"
    return Path.home() / f".{APP_DIR_NAME}" / "config.json"


def load_app_config(path: Path | None = None) -> AppConfig:
    path = path or default_config_path()
    if not path.exists():
        return AppConfig()
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    return AppConfig(
        converter=ConverterConfig(**data.get("converter", {})),
        llm=LLMConfig.from_dict(data.get("llm", {})),
        template_path=str(data.get("template_path", "")),
        output_dir=str(data.get("output_dir", "")),
        recursive=bool(data.get("recursive", True)),
    )


def save_app_config(config: AppConfig, path: Path | None = None) -> None:
    path = path or default_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    data: dict[str, Any] = {
        "converter": {
            "executable_path": config.converter.executable_path,
            "output_version": config.converter.output_version,
            "audit": config.converter.audit,
        },
        "llm": config.llm.to_dict(),
        "template_path": config.template_path,
        "output_dir": config.output_dir,
        "recursive": config.recursive,
    }
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
