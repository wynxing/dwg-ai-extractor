from __future__ import annotations

import platform
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import ezdxf

_CONVERTER_EXE = "ODAFileConverter.exe" if platform.system() == "Windows" else "ODAFileConverter"

from .models import ConverterConfig, DrawingContext, TextRecord


SUPPORTED_SUFFIXES = {".dwg", ".dxf"}


class ConversionError(RuntimeError):
    pass


def scan_input_paths(input_paths: list[Path], recursive: bool = True) -> list[Path]:
    files: list[Path] = []
    for input_path in input_paths:
        path = input_path.expanduser()
        if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES:
            files.append(path.resolve())
        elif path.is_dir():
            iterator = path.rglob("*") if recursive else path.glob("*")
            files.extend(item.resolve() for item in iterator if item.is_file() and item.suffix.lower() in SUPPORTED_SUFFIXES)
    return sorted(set(files), key=lambda item: str(item).casefold())


def read_drawing_context(path: Path, converter: ConverterConfig) -> DrawingContext:
    temporary_dxf: Path | None = None
    try:
        dxf_path = path
        if path.suffix.lower() == ".dwg":
            dxf_path = convert_dwg_to_dxf(path, converter)
            temporary_dxf = dxf_path
        if dxf_path.suffix.lower() != ".dxf":
            raise ValueError(f"不支持的文件类型：{path.suffix}")
        return DrawingContext(file_path=path, records=read_dxf_text_records(dxf_path))
    finally:
        if temporary_dxf is not None:
            shutil.rmtree(temporary_dxf.parent, ignore_errors=True)


def convert_dwg_to_dxf(dwg_path: Path, config: ConverterConfig) -> Path:
    executable = resolve_converter_executable(config.executable_path)
    if executable is None:
        raise ConversionError(f"未配置可用的 {_CONVERTER_EXE}，无法处理 DWG 文件")

    with tempfile.TemporaryDirectory(prefix="dwg_ai_extract_") as temp_dir:
        temp_root = Path(temp_dir)
        input_dir = temp_root / "input"
        output_dir = temp_root / "output"
        input_dir.mkdir()
        output_dir.mkdir()
        staged_dwg = input_dir / dwg_path.name
        shutil.copy2(dwg_path, staged_dwg)

        command = [
            str(executable),
            str(input_dir),
            str(output_dir),
            config.output_version,
            "DXF",
            "0",
            "1" if config.audit else "0",
        ]
        completed = subprocess.run(command, capture_output=True, text=True, timeout=300, check=False)
        if completed.returncode != 0:
            message = (completed.stderr or completed.stdout or "").strip()
            raise ConversionError(f"DWG 转 DXF 失败：{message or f'退出码 {completed.returncode}'}")

        converted = _find_converted_dxf(output_dir, dwg_path.stem)
        if converted is None:
            raise ConversionError("DWG 转换完成但未找到输出 DXF 文件")

        stable_temp_dir = Path(tempfile.mkdtemp(prefix="dwg_ai_extract_dxf_"))
        stable_path = stable_temp_dir / converted.name
        shutil.copy2(converted, stable_path)
        return stable_path


def resolve_converter_executable(path_value: str) -> Path | None:
    if not path_value:
        return None
    path = Path(path_value).expanduser()
    if path.is_file():
        return path
    if path.is_dir():
        candidate = path / _CONVERTER_EXE
        if candidate.is_file():
            return candidate
    return None


def read_dxf_text_records(path: Path) -> list[TextRecord]:
    doc = ezdxf.readfile(path)
    records: list[TextRecord] = []
    for layout in doc.layouts:
        for entity in layout:
            records.extend(_records_from_entity(entity, layout.name))
    records.extend(_read_block_definition_records(doc))
    return [record for record in records if record.text.strip()]


def _read_block_definition_records(doc: Any) -> list[TextRecord]:
    records: list[TextRecord] = []
    for block in doc.blocks:
        if block.name in {"*Model_Space", "*Paper_Space", "*Paper_Space0"}:
            continue
        for entity in block:
            for record in _records_from_entity(entity, f"Block:{block.name}"):
                if not record.block_name:
                    record.block_name = block.name
                records.append(record)
    return records


def _records_from_entity(entity: Any, source_space: str) -> list[TextRecord]:
    entity_type = entity.dxftype()
    if entity_type == "TEXT":
        return [_record(entity.dxf.text, entity, source_space, entity_type=entity_type)]
    if entity_type == "MTEXT":
        text = entity.plain_text() if hasattr(entity, "plain_text") else entity.text
        return [_record(text, entity, source_space, entity_type=entity_type)]
    if entity_type in {"ATTRIB", "ATTDEF"}:
        return [_record(entity.dxf.text, entity, source_space, entity_type=entity_type)]
    if entity_type == "INSERT":
        block_name = getattr(entity.dxf, "name", "")
        return [_record(attrib.dxf.text, attrib, source_space, block_name=block_name, entity_type="ATTRIB") for attrib in getattr(entity, "attribs", [])]
    return []


def _record(
    text: str,
    entity: Any,
    source_space: str,
    *,
    block_name: str = "",
    entity_type: str = "",
) -> TextRecord:
    insert = getattr(entity.dxf, "insert", None)
    return TextRecord(
        text=str(text or ""),
        source_space=source_space,
        layer=str(getattr(entity.dxf, "layer", "") or ""),
        block_name=block_name,
        entity_type=entity_type,
        x=_coord(insert, 0),
        y=_coord(insert, 1),
        z=_coord(insert, 2),
    )


def _coord(point: Any, index: int) -> float | None:
    if point is None:
        return None
    try:
        return float(point[index])
    except (TypeError, IndexError, ValueError):
        return None


def _find_converted_dxf(output_dir: Path, stem: str) -> Path | None:
    exact = list(output_dir.rglob(f"{stem}.dxf")) + list(output_dir.rglob(f"{stem}.DXF"))
    if exact:
        return exact[0]
    dxfs = sorted(output_dir.rglob("*.dxf")) + sorted(output_dir.rglob("*.DXF"))
    return dxfs[0] if dxfs else None
