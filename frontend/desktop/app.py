from __future__ import annotations

import platform
from pathlib import Path
from threading import Event

from PySide6.QtCore import QObject, QThread, Signal, Slot
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from backend.batch_processor import BatchProcessor
from backend.config_store import load_app_config, save_app_config
from backend.field_templates import DEFAULT_TEMPLATE, load_template, save_template, validate_template
from backend.llm_client import OpenAICompatibleClient
from backend.models import AppConfig, BatchJob, ConverterConfig, ExtractionResult, FieldSpec, LLMConfig
from frontend.desktop.panels import BatchPanel, ModelPanel, ResultPanel, TemplatePanel


class BatchWorker(QObject):
    progress = Signal(int, int, object, str)
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, job: BatchJob, cancel_event: Event) -> None:
        super().__init__()
        self.job = job
        self.cancel_event = cancel_event

    @Slot()
    def run(self) -> None:
        try:
            results = BatchProcessor(self.job, self.cancel_event).run(self.progress.emit)
            self.finished.emit(results)
        except Exception as exc:  # noqa: BLE001 - top-level GUI worker reporting.
            self.failed.emit(str(exc))


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("DWG AI 字段抽取系统")
        self.resize(1280, 820)
        self.config = load_app_config()
        self.template = DEFAULT_TEMPLATE
        self.thread: QThread | None = None
        self.worker: BatchWorker | None = None
        self.cancel_event: Event | None = None
        self._build_ui()
        self._load_config_to_ui()
        self._refresh_template_table()
        self._refresh_result_table_columns()

    def _build_ui(self) -> None:
        root = QWidget(self)
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)

        top_row = QHBoxLayout()
        layout.addLayout(top_row)
        self.batch_panel = BatchPanel(self)
        self.model_panel = ModelPanel(self)
        self.template_panel = TemplatePanel(self)
        self.result_panel = ResultPanel(self)

        top_row.addWidget(self.batch_panel, 2)
        top_row.addWidget(self.model_panel, 1)
        layout.addWidget(self.template_panel, 2)
        layout.addWidget(self.result_panel, 3)

        self._bind_panel_widgets()
        self._connect_panel_signals()

    def _bind_panel_widgets(self) -> None:
        self.input_list = self.batch_panel.input_list
        self.output_edit = self.batch_panel.output_edit
        self.converter_edit = self.batch_panel.converter_edit
        self.recursive_check = self.batch_panel.recursive_check
        self.start_button = self.batch_panel.start_button
        self.cancel_button = self.batch_panel.cancel_button

        self.base_url_edit = self.model_panel.base_url_edit
        self.api_env_edit = self.model_panel.api_env_edit
        self.model_edit = self.model_panel.model_edit
        self.temperature_spin = self.model_panel.temperature_spin
        self.timeout_spin = self.model_panel.timeout_spin
        self.retry_spin = self.model_panel.retry_spin
        self.json_mode_check = self.model_panel.json_mode_check

        self.template_path_edit = self.template_panel.template_path_edit
        self.template_table = self.template_panel.template_table

        self.progress_bar = self.result_panel.progress_bar
        self.result_table = self.result_panel.result_table
        self.log_edit = self.result_panel.log_edit

    def _connect_panel_signals(self) -> None:
        self.batch_panel.add_files_button.clicked.connect(self.add_files)
        self.batch_panel.add_folder_button.clicked.connect(self.add_folder)
        self.batch_panel.remove_button.clicked.connect(self.remove_selected_inputs)
        self.batch_panel.clear_button.clicked.connect(self.input_list.clear)
        self.batch_panel.output_button.clicked.connect(self.choose_output)
        self.batch_panel.converter_button.clicked.connect(self.choose_converter)
        self.start_button.clicked.connect(self.start_batch)
        self.cancel_button.clicked.connect(self.cancel_batch)

        self.model_panel.test_button.clicked.connect(self.test_model_connection)

        self.template_panel.load_template_button.clicked.connect(self.load_template_from_file)
        self.template_panel.save_template_button.clicked.connect(self.save_template_to_file)
        self.template_panel.add_field_button.clicked.connect(self.add_template_field)
        self.template_panel.remove_field_button.clicked.connect(self.remove_template_field)

    def _load_config_to_ui(self) -> None:
        self.converter_edit.setText(self.config.converter.executable_path)
        self.base_url_edit.setText(self.config.llm.base_url)
        self.api_env_edit.setText(self.config.llm.api_key_env_var)
        self.model_edit.setText(self.config.llm.model)
        self.temperature_spin.setValue(self.config.llm.temperature)
        self.timeout_spin.setValue(self.config.llm.timeout_seconds)
        self.retry_spin.setValue(self.config.llm.max_retries)
        self.json_mode_check.setChecked(self.config.llm.use_json_object)
        self.recursive_check.setChecked(self.config.recursive)
        self.template_path_edit.setText(self.config.template_path)
        if self.config.template_path and Path(self.config.template_path).exists():
            try:
                self.template = load_template(Path(self.config.template_path))
            except Exception as exc:  # noqa: BLE001 - user-facing config recovery.
                QMessageBox.warning(self, "模板加载失败", str(exc))
        if self.config.output_dir:
            self.output_edit.setText(str(Path(self.config.output_dir) / "字段抽取结果.xlsx"))

    def add_files(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(self, "选择 DWG/DXF 文件", "", "CAD Files (*.dwg *.dxf)")
        for file_name in files:
            self._add_input(file_name)
        self._suggest_output_path()

    def add_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "选择目录")
        if folder:
            self._add_input(folder)
            self._suggest_output_path()

    def remove_selected_inputs(self) -> None:
        for item in self.input_list.selectedItems():
            self.input_list.takeItem(self.input_list.row(item))

    def choose_output(self) -> None:
        file_name, _ = QFileDialog.getSaveFileName(self, "选择输出 Excel", self.output_edit.text(), "Excel Files (*.xlsx)")
        if file_name:
            self.output_edit.setText(file_name if file_name.lower().endswith(".xlsx") else f"{file_name}.xlsx")

    def choose_converter(self) -> None:
        exe_filter = "Executable (*.exe)" if platform.system() == "Windows" else "Executable (*)"
        file_name, _ = QFileDialog.getOpenFileName(self, "选择 ODAFileConverter", "", exe_filter)
        if file_name:
            self.converter_edit.setText(file_name)

    def load_template_from_file(self) -> None:
        file_name, _ = QFileDialog.getOpenFileName(self, "加载字段模板", self.template_path_edit.text(), "JSON Files (*.json)")
        if file_name:
            try:
                self.template = load_template(Path(file_name))
            except Exception as exc:  # noqa: BLE001 - user-facing template validation.
                QMessageBox.critical(self, "模板加载失败", str(exc))
                return
            else:
                self.template_path_edit.setText(file_name)
                self._refresh_template_table()
                self._refresh_result_table_columns()

    def save_template_to_file(self) -> None:
        try:
            self._template_from_table()
        except Exception as exc:  # noqa: BLE001 - user-facing template validation.
            QMessageBox.critical(self, "模板无效", str(exc))
            return
        file_name, _ = QFileDialog.getSaveFileName(self, "保存字段模板", self.template_path_edit.text(), "JSON Files (*.json)")
        if file_name:
            path = Path(file_name if file_name.lower().endswith(".json") else f"{file_name}.json")
            try:
                save_template(self.template, path)
            except Exception as exc:  # noqa: BLE001 - user-facing template validation.
                QMessageBox.critical(self, "模板保存失败", str(exc))
                return
            self.template_path_edit.setText(str(path))

    def add_template_field(self) -> None:
        row = self.template_table.rowCount()
        self.template_table.insertRow(row)
        defaults = [f"field_{row + 1}", f"字段{row + 1}", "", "false", "", "strip"]
        for col, value in enumerate(defaults):
            self.template_table.setItem(row, col, QTableWidgetItem(value))
        self._refresh_result_table_columns()

    def remove_template_field(self) -> None:
        rows = sorted({item.row() for item in self.template_table.selectedItems()}, reverse=True)
        for row in rows:
            self.template_table.removeRow(row)
        self._template_from_table(validate=False)
        self._refresh_result_table_columns()

    def start_batch(self) -> None:
        input_paths = [Path(self.input_list.item(index).text()) for index in range(self.input_list.count())]
        if not input_paths:
            QMessageBox.warning(self, "缺少输入", "请先添加 DWG/DXF 文件或目录。")
            return
        if not self.output_edit.text().strip():
            QMessageBox.warning(self, "缺少输出", "请选择输出 Excel 路径。")
            return
        try:
            self._template_from_table()
        except Exception as exc:  # noqa: BLE001 - user-facing template validation.
            QMessageBox.critical(self, "模板无效", str(exc))
            return
        self._save_ui_config()
        job = BatchJob(
            input_paths=input_paths,
            output_excel_path=Path(self.output_edit.text().strip()),
            template=self.template,
            llm=self._llm_from_ui(),
            converter=ConverterConfig(executable_path=self.converter_edit.text().strip()),
            recursive=self.recursive_check.isChecked(),
        )
        self.result_table.setRowCount(0)
        self.progress_bar.setValue(0)
        self.log_edit.clear()
        self.cancel_event = Event()
        self.thread = QThread(self)
        self.worker = BatchWorker(job, self.cancel_event)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_finished)
        self.worker.failed.connect(self.on_failed)
        self.worker.finished.connect(self.thread.quit)
        self.worker.failed.connect(self.thread.quit)
        self.thread.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(self._clear_thread_refs)
        self._set_running(True)
        self.thread.start()

    def cancel_batch(self) -> None:
        if self.cancel_event:
            self.cancel_event.set()
            self.cancel_button.setEnabled(False)
            self._append_log("正在取消，当前文件处理结束后停止。")

    def test_model_connection(self) -> None:
        try:
            OpenAICompatibleClient(self._llm_from_ui()).test_connection()
            QMessageBox.information(self, "测试成功", "模型连接测试成功。")
        except Exception as exc:  # noqa: BLE001 - user-facing connection test.
            QMessageBox.critical(self, "测试失败", str(exc))

    @Slot(int, int, object, str)
    def on_progress(self, current: int, total: int, result: ExtractionResult | None, message: str) -> None:
        if total:
            self.progress_bar.setValue(int(current / total * 100))
        if result:
            if result.status == "成功":
                self._append_result_row(result)
                self._append_log(f"{result.file_path.name} - 成功")
            else:
                self._append_log(f"{result.file_path.name} - 失败：{result.error}")
        else:
            self._append_log(message)

    @Slot(object)
    def on_finished(self, results: list[ExtractionResult]) -> None:
        self._set_running(False)
        success_count = sum(1 for result in results if result.status == "成功")
        self.progress_bar.setValue(100)
        self._append_log(f"完成：成功 {success_count}，失败 {len(results) - success_count}。")
        self._append_log(f"Excel 已输出：{self.output_edit.text()}")
        QMessageBox.information(self, "处理完成", f"成功 {success_count}，失败 {len(results) - success_count}。")

    @Slot(str)
    def on_failed(self, message: str) -> None:
        self._set_running(False)
        QMessageBox.critical(self, "处理失败", message)

    @Slot()
    def _clear_thread_refs(self) -> None:
        self.thread = None
        self.worker = None
        self.cancel_event = None

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt override name.
        if self.thread and self.thread.isRunning():
            QMessageBox.warning(self, "正在处理", "请先取消或等待当前批处理完成。")
            event.ignore()
            return
        self._save_ui_config()
        event.accept()

    def _refresh_template_table(self) -> None:
        self.template_table.setRowCount(0)
        for field in self.template.fields:
            row = self.template_table.rowCount()
            self.template_table.insertRow(row)
            values = [field.key, field.label, field.description, str(field.required).lower(), field.example, field.postprocess]
            for col, value in enumerate(values):
                self.template_table.setItem(row, col, QTableWidgetItem(value))

    def _template_from_table(self, validate: bool = True) -> None:
        fields = []
        for row in range(self.template_table.rowCount()):
            cells = [self.template_table.item(row, col).text().strip() if self.template_table.item(row, col) else "" for col in range(6)]
            fields.append(FieldSpec(cells[0], cells[1], cells[2], cells[3].lower() in {"true", "1", "yes", "是"}, cells[4], cells[5] or "strip"))
        self.template.fields = fields
        if validate:
            validate_template(self.template)

    def _refresh_result_table_columns(self) -> None:
        self._template_from_table(validate=False)
        self.result_table.setColumnCount(len(self.template.fields))
        self.result_table.setHorizontalHeaderLabels([field.label for field in self.template.fields])

    def _append_result_row(self, result: ExtractionResult) -> None:
        row = self.result_table.rowCount()
        self.result_table.insertRow(row)
        for col, field in enumerate(self.template.fields):
            self.result_table.setItem(row, col, QTableWidgetItem(result.values.get(field.key, "")))

    def _llm_from_ui(self) -> LLMConfig:
        return LLMConfig(
            base_url=self.base_url_edit.text().strip(),
            api_key_env_var=self.api_env_edit.text().strip(),
            model=self.model_edit.text().strip(),
            temperature=self.temperature_spin.value(),
            timeout_seconds=self.timeout_spin.value(),
            max_retries=self.retry_spin.value(),
            use_json_object=self.json_mode_check.isChecked(),
        )

    def _save_ui_config(self) -> None:
        self.config = AppConfig(
            converter=ConverterConfig(executable_path=self.converter_edit.text().strip()),
            llm=self._llm_from_ui(),
            template_path=self.template_path_edit.text().strip(),
            output_dir=str(Path(self.output_edit.text().strip()).parent) if self.output_edit.text().strip() else "",
            recursive=self.recursive_check.isChecked(),
        )
        save_app_config(self.config)

    def _add_input(self, value: str) -> None:
        existing = {self.input_list.item(index).text() for index in range(self.input_list.count())}
        if value not in existing:
            self.input_list.addItem(value)

    def _suggest_output_path(self) -> None:
        if self.output_edit.text().strip() or self.input_list.count() == 0:
            return
        first = Path(self.input_list.item(0).text())
        base_dir = first if first.is_dir() else first.parent
        self.output_edit.setText(str(base_dir / "字段抽取结果.xlsx"))

    def _set_running(self, running: bool) -> None:
        self.start_button.setEnabled(not running)
        self.cancel_button.setEnabled(running)

    def _append_log(self, message: str) -> None:
        self.log_edit.append(message)


def main() -> int:
    app = QApplication([])
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
