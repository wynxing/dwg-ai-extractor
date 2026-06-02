from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTextEdit,
    QVBoxLayout,
)


class BatchPanel(QGroupBox):
    def __init__(self, parent=None) -> None:
        super().__init__("批处理", parent)
        layout = QGridLayout(self)
        self.input_list = QListWidget()
        layout.addWidget(QLabel("待处理文件/目录"), 0, 0)
        layout.addWidget(self.input_list, 1, 0, 6, 1)

        self.add_files_button = QPushButton("添加文件")
        self.add_folder_button = QPushButton("添加目录")
        self.remove_button = QPushButton("移除选中")
        self.clear_button = QPushButton("清空")
        button_col = QVBoxLayout()
        for button in [self.add_files_button, self.add_folder_button, self.remove_button, self.clear_button]:
            button_col.addWidget(button)
        button_col.addStretch(1)
        layout.addLayout(button_col, 1, 1)

        self.output_edit = QLineEdit()
        self.output_button = QPushButton("选择")
        layout.addWidget(QLabel("输出 Excel"), 1, 2)
        layout.addWidget(self.output_edit, 1, 3)
        layout.addWidget(self.output_button, 1, 4)

        self.converter_edit = QLineEdit()
        self.converter_button = QPushButton("选择")
        layout.addWidget(QLabel("ODA 转换器"), 2, 2)
        layout.addWidget(self.converter_edit, 2, 3)
        layout.addWidget(self.converter_button, 2, 4)

        self.recursive_check = QCheckBox("递归扫描目录")
        layout.addWidget(self.recursive_check, 3, 3)

        action_row = QHBoxLayout()
        self.start_button = QPushButton("开始处理")
        self.cancel_button = QPushButton("取消")
        self.cancel_button.setEnabled(False)
        action_row.addWidget(self.start_button)
        action_row.addWidget(self.cancel_button)
        action_row.addStretch(1)
        layout.addLayout(action_row, 4, 3, 1, 2)


class ModelPanel(QGroupBox):
    def __init__(self, parent=None) -> None:
        super().__init__("模型配置", parent)
        layout = QGridLayout(self)
        self.base_url_edit = QLineEdit()
        self.api_env_edit = QLineEdit()
        self.model_edit = QLineEdit()
        self.temperature_spin = QDoubleSpinBox()
        self.temperature_spin.setRange(0, 2)
        self.temperature_spin.setSingleStep(0.1)
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(5, 600)
        self.retry_spin = QSpinBox()
        self.retry_spin.setRange(0, 10)
        self.json_mode_check = QCheckBox("启用 JSON object 模式")
        self.test_button = QPushButton("测试连接")

        rows = [
            ("Base URL", self.base_url_edit),
            ("API Key 环境变量名", self.api_env_edit),
            ("Model", self.model_edit),
            ("Temperature", self.temperature_spin),
            ("Timeout 秒", self.timeout_spin),
            ("Max Retries", self.retry_spin),
        ]
        for row, (label, widget) in enumerate(rows):
            layout.addWidget(QLabel(label), row, 0)
            layout.addWidget(widget, row, 1)
        layout.addWidget(self.json_mode_check, len(rows), 1)
        layout.addWidget(self.test_button, len(rows) + 1, 1)
        note = QPlainTextEdit("注意：这里填写的是环境变量名，不是 API Key 明文。程序运行时从该环境变量读取真实密钥。")
        note.setReadOnly(True)
        note.setMaximumHeight(70)
        layout.addWidget(note, len(rows) + 2, 0, 1, 2)


class TemplatePanel(QGroupBox):
    def __init__(self, parent=None) -> None:
        super().__init__("字段模板", parent)
        layout = QVBoxLayout(self)
        buttons = QHBoxLayout()
        self.template_path_edit = QLineEdit()
        self.load_template_button = QPushButton("加载模板")
        self.save_template_button = QPushButton("保存模板")
        self.add_field_button = QPushButton("新增字段")
        self.remove_field_button = QPushButton("删除选中")
        buttons.addWidget(QLabel("模板文件"))
        buttons.addWidget(self.template_path_edit, 1)
        buttons.addWidget(self.load_template_button)
        buttons.addWidget(self.save_template_button)
        buttons.addWidget(self.add_field_button)
        buttons.addWidget(self.remove_field_button)
        layout.addLayout(buttons)

        self.template_table = QTableWidget(0, 6)
        self.template_table.setHorizontalHeaderLabels(["key", "表头", "说明", "必填", "示例", "后处理"])
        self.template_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.template_table)


class ResultPanel(QGroupBox):
    def __init__(self, parent=None) -> None:
        super().__init__("结果预览与日志", parent)
        layout = QVBoxLayout(self)
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)
        self.result_table = QTableWidget()
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.result_table, 2)
        self.log_edit = QTextEdit()
        self.log_edit.setReadOnly(True)
        self.log_edit.setMaximumHeight(150)
        layout.addWidget(self.log_edit)
