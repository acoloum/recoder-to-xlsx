"""PyQt5 主視窗。"""
from __future__ import annotations

from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QCheckBox,
    QDateTimeEdit,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from .worker import ConvertJob, ConvertWorker, LoadMetadataWorker


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("無紙紀錄器轉檔程式")
        self.resize(720, 600)
        self._worker: ConvertWorker | None = None
        self._loader: LoadMetadataWorker | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        form = QFormLayout()

        # 輸入資料夾
        in_layout = QHBoxLayout()
        self.input_edit = QLineEdit()
        in_btn = QPushButton("瀏覽…")
        in_btn.clicked.connect(self._choose_input)
        in_layout.addWidget(self.input_edit)
        in_layout.addWidget(in_btn)
        form.addRow("輸入資料夾", in_layout)

        # 輸出 xlsx
        out_layout = QHBoxLayout()
        self.output_edit = QLineEdit()
        out_btn = QPushButton("瀏覽…")
        out_btn.clicked.connect(self._choose_output)
        out_layout.addWidget(self.output_edit)
        out_layout.addWidget(out_btn)
        form.addRow("輸出 .xlsx", out_layout)

        # 時段
        self.start_edit = QDateTimeEdit()
        self.end_edit = QDateTimeEdit()
        self.start_edit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.end_edit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.full_range_cb = QCheckBox("全部時段")
        self.full_range_cb.setChecked(True)
        self.full_range_cb.toggled.connect(self._toggle_range)
        form.addRow("起始時間", self.start_edit)
        form.addRow("結束時間", self.end_edit)
        form.addRow("", self.full_range_cb)
        self._toggle_range(True)

        # 通道
        ch_layout = QVBoxLayout()
        self.channel_list = QListWidget()
        self.channel_list.setSelectionMode(QListWidget.MultiSelection)
        ch_btn_layout = QHBoxLayout()
        select_all_btn = QPushButton("全選")
        select_all_btn.clicked.connect(self.channel_list.selectAll)
        deselect_all_btn = QPushButton("取消全選")
        deselect_all_btn.clicked.connect(self.channel_list.clearSelection)
        ch_btn_layout.addWidget(select_all_btn)
        ch_btn_layout.addWidget(deselect_all_btn)
        ch_btn_layout.addStretch()
        ch_layout.addLayout(ch_btn_layout)
        ch_layout.addWidget(self.channel_list)
        form.addRow("選擇通道", ch_layout)

        # 間隔
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 86400)
        self.interval_spin.setValue(120)
        self.interval_spin.setSuffix(" 秒")
        form.addRow("資料間隔", self.interval_spin)

        # 顯示空白
        self.blanks_cb = QCheckBox("顯示空白數值")
        self.blanks_cb.setChecked(True)
        form.addRow("", self.blanks_cb)

        # 事件
        self.events_cb = QCheckBox("輸出事件")
        self.events_cb.setChecked(True)
        form.addRow("", self.events_cb)

        form.addRow("日期格式", QLabel("yyyy-mm-dd（固定）"))

        root.addLayout(form)

        # 轉檔按鈕
        self.run_btn = QPushButton("轉檔")
        self.run_btn.clicked.connect(self._run)
        root.addWidget(self.run_btn)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)
        root.addWidget(self.progress)

        self.setStatusBar(QStatusBar())

    def _toggle_range(self, full: bool) -> None:
        self.start_edit.setEnabled(not full)
        self.end_edit.setEnabled(not full)

    def _choose_input(self) -> None:
        d = QFileDialog.getExistingDirectory(self, "選擇紀錄器資料夾")
        if d:
            self.input_edit.setText(d)
            self._start_load_metadata(Path(d))

    def _choose_output(self) -> None:
        f, _ = QFileDialog.getSaveFileName(self, "輸出 .xlsx", "", "Excel (*.xlsx)")
        if f:
            if not f.lower().endswith(".xlsx"):
                f += ".xlsx"
            self.output_edit.setText(f)

    def _start_load_metadata(self, folder: Path) -> None:
        """在背景執行緒載入 metadata，避免 GUI 凍結。"""
        if self._loader is not None and self._loader.isRunning():
            return
        self.run_btn.setEnabled(False)
        self.statusBar().showMessage("正在讀取資料夾…")
        self._loader = LoadMetadataWorker(folder)
        self._loader.progress.connect(self.statusBar().showMessage)
        self._loader.finished_ok.connect(lambda data: self._on_metadata_loaded(folder, data))
        self._loader.failed.connect(self._on_metadata_failed)
        self._loader.start()

    def _on_metadata_loaded(self, folder: Path, data: object) -> None:
        self.run_btn.setEnabled(True)
        self.channel_list.clear()
        for ch in data.channels:
            item = QListWidgetItem(ch.name)
            item.setSelected(True)
            self.channel_list.addItem(item)

        all_ts = [s.timestamp for ch in data.samples.values() for s in ch]
        if all_ts:
            self.start_edit.setDateTime(min(all_ts))
            self.end_edit.setDateTime(max(all_ts))

        if not self.output_edit.text():
            self.output_edit.setText(str(folder.parent / f"{folder.name}.xlsx"))

        self.statusBar().showMessage(f"已載入 {len(data.channels)} 通道")

    def _on_metadata_failed(self, msg: str) -> None:
        self.run_btn.setEnabled(True)
        QMessageBox.critical(self, "錯誤", f"無法讀取資料夾：{msg}")

    def _run(self) -> None:
        if self._worker is not None and self._worker.isRunning():
            return
        if not self.input_edit.text() or not self.output_edit.text():
            QMessageBox.warning(self, "提示", "請選輸入資料夾與輸出檔")
            return

        selected = [
            i
            for i in range(self.channel_list.count())
            if self.channel_list.item(i).isSelected()
        ]
        if not selected:
            QMessageBox.warning(self, "提示", "請至少選一個通道")
            return

        full = self.full_range_cb.isChecked()
        job = ConvertJob(
            input_folder=Path(self.input_edit.text()),
            output_path=Path(self.output_edit.text()),
            interval_seconds=self.interval_spin.value(),
            start=None if full else self.start_edit.dateTime().toPyDateTime(),
            end=None if full else self.end_edit.dateTime().toPyDateTime(),
            selected_channels=selected,
            show_blanks=self.blanks_cb.isChecked(),
            include_events=self.events_cb.isChecked(),
        )

        self._worker = ConvertWorker(job)
        self._worker.progress.connect(lambda m: self.statusBar().showMessage(m))
        self._worker.finished_ok.connect(self._on_done)
        self._worker.failed.connect(self._on_fail)
        self.progress.setVisible(True)
        self.run_btn.setEnabled(False)
        self._worker.start()

    def _on_done(self, count: int, path: str) -> None:
        self.progress.setVisible(False)
        self.run_btn.setEnabled(True)
        self.statusBar().showMessage("完成")
        QMessageBox.information(self, "完成", f"轉檔成功，共 {count} 筆\n輸出於 {path}")

    def _on_fail(self, msg: str) -> None:
        self.progress.setVisible(False)
        self.run_btn.setEnabled(True)
        self.statusBar().showMessage("失敗")
        QMessageBox.critical(self, "錯誤", msg)
