from __future__ import annotations

import argparse
import json
from pathlib import Path

from .batch_processor import BatchProcessor
from .field_templates import load_template
from .models import BatchJob, ConverterConfig, LLMConfig


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="字段模板驱动的 DWG/DXF AI 信息抽取")
    parser.add_argument("--input", "-i", action="append", required=True, help="输入 DWG/DXF 文件或目录，可重复指定")
    parser.add_argument("--output", "-o", required=True, help="输出 Excel 路径")
    parser.add_argument("--template", "-t", default="", help="字段模板 JSON 路径，留空使用默认模板")
    parser.add_argument("--llm-config", required=True, help="模型配置 JSON 路径")
    parser.add_argument("--converter", "-c", default="", help="ODAFileConverter.exe 路径，仅 DWG 需要")
    parser.add_argument("--recursive", action=argparse.BooleanOptionalAction, default=True, help="是否递归扫描目录")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    template = load_template(Path(args.template)) if args.template else load_template()
    with Path(args.llm_config).open("r", encoding="utf-8") as file:
        llm = LLMConfig.from_dict(json.load(file))
    job = BatchJob(
        input_paths=[Path(value) for value in args.input],
        output_excel_path=Path(args.output),
        template=template,
        llm=llm,
        converter=ConverterConfig(executable_path=args.converter),
        recursive=args.recursive,
    )

    def print_progress(current: int, total: int, _result, message: str) -> None:
        print(f"[{current}/{total}] {message}")

    results = BatchProcessor(job).run(print_progress)
    success_count = sum(1 for result in results if result.status == "成功")
    print(f"完成：成功 {success_count}，失败 {len(results) - success_count}，输出 {job.output_excel_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
