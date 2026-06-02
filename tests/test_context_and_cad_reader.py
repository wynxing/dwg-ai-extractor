from pathlib import Path

import ezdxf

from backend.cad_reader import read_dxf_text_records, scan_input_paths
from backend.context_builder import build_llm_context
from backend.models import DrawingContext, TextRecord


def test_reads_dxf_text_attributes_and_block_definition_text(tmp_path: Path) -> None:
    dxf_path = tmp_path / "sample.dxf"
    doc = ezdxf.new()
    msp = doc.modelspace()
    msp.add_text("物料编码: ABC-123", dxfattribs={"height": 2.5}).set_placement((0, 0))
    block = doc.blocks.new(name="TITLE")
    block.add_mtext("零件名称", dxfattribs={"insert": (0, 0), "char_height": 2.5})
    block.add_mtext("指示镜片", dxfattribs={"insert": (20, 0), "char_height": 2.5})
    block.add_attdef("MATERIAL", insert=(0, -10), text="材料: PC", dxfattribs={"height": 2.5})
    insert = msp.add_blockref("TITLE", (0, 20))
    insert.add_auto_attribs({"MATERIAL": "材料: PC"})
    msp.add_line((0, 0), (1, 1))
    doc.saveas(dxf_path)

    records = read_dxf_text_records(dxf_path)
    texts = [record.text for record in records]

    assert "物料编码: ABC-123" in texts
    assert "材料: PC" in texts
    assert "零件名称" in texts
    assert "指示镜片" in texts
    assert any(record.block_name == "TITLE" for record in records)


def test_context_contains_only_text_metadata(tmp_path: Path) -> None:
    dxf_path = tmp_path / "sample.dxf"
    doc = ezdxf.new()
    doc.modelspace().add_text("技术要求：材料 PC", dxfattribs={"height": 2.5}).set_placement((1, 2))
    doc.saveas(dxf_path)

    records = read_dxf_text_records(dxf_path)
    context = build_llm_context(DrawingContext(dxf_path, records))

    assert context["file_name"] == "sample.dxf"
    assert "file_path_hint" not in context
    assert "text_records" in context
    assert context["text_records"][0]["text"] == "技术要求：材料 PC"
    assert "binary" not in str(context).lower()


def test_context_can_include_file_path_hint_when_requested(tmp_path: Path) -> None:
    dxf_path = tmp_path / "sample.dxf"
    context = build_llm_context(DrawingContext(dxf_path, [TextRecord("材料 PC", "Model")]), include_file_path_hint=True)

    assert context["file_path_hint"] == str(dxf_path)


def test_context_prioritizes_title_and_technical_records_before_truncation(tmp_path: Path) -> None:
    records = [TextRecord(f"普通标注 {index}", "Model", y=float(index)) for index in range(20)]
    records.append(TextRecord("技术要求：材料 PC，表面处理喷油", "Model", layer="NOTES", y=-100))
    context = build_llm_context(DrawingContext(tmp_path / "sample.dxf", records), max_records=1)

    assert context["text_records"][0]["text"] == "技术要求：材料 PC，表面处理喷油"


def test_scan_input_paths_filters_supported_files(tmp_path: Path) -> None:
    dxf = tmp_path / "a.dxf"
    dwg = tmp_path / "b.dwg"
    txt = tmp_path / "c.txt"
    for path in [dxf, dwg, txt]:
        path.write_text("", encoding="utf-8")

    files = scan_input_paths([tmp_path], recursive=False)

    assert files == sorted([dxf.resolve(), dwg.resolve()], key=lambda item: str(item).casefold())
