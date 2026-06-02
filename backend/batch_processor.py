from __future__ import annotations

import time
from collections.abc import Callable
from pathlib import Path
from threading import Event

from .cad_reader import read_drawing_context, scan_input_paths
from .excel_exporter import export_results_to_excel
from .extractor import extract_fields_with_llm
from .models import BatchJob, ExtractionResult


ProgressCallback = Callable[[int, int, ExtractionResult | None, str], None]


class BatchProcessor:
    def __init__(self, job: BatchJob, cancel_event: Event | None = None) -> None:
        self.job = job
        self.cancel_event = cancel_event or Event()

    def run(self, progress: ProgressCallback | None = None) -> list[ExtractionResult]:
        files = scan_input_paths(self.job.input_paths, self.job.recursive)
        results: list[ExtractionResult] = []
        success_sequence = 1
        total = len(files)
        for index, file_path in enumerate(files, start=1):
            if self.cancel_event.is_set():
                if progress:
                    progress(index - 1, total, None, "已取消")
                break
            result = self.process_file(file_path, success_sequence)
            if result.status == "成功":
                success_sequence += 1
            results.append(result)
            if progress:
                progress(index, total, result, f"{index}/{total} {file_path.name}")

        export_results_to_excel(results, self.job.template, self.job.output_excel_path)
        return results

    def process_file(self, file_path: Path, sequence: int) -> ExtractionResult:
        started = time.perf_counter()
        try:
            context = read_drawing_context(file_path, self.job.converter)
            values = extract_fields_with_llm(context, self.job.template, self.job.llm, sequence)
            return ExtractionResult(file_path=file_path, status="成功", values=values, elapsed_seconds=time.perf_counter() - started)
        except Exception as exc:  # noqa: BLE001 - batch processing isolates per-file failures.
            return ExtractionResult(file_path=file_path, status="失败", error=str(exc), elapsed_seconds=time.perf_counter() - started)
