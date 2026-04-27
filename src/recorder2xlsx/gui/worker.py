"""背景轉檔 worker（QThread），避免 GUI 凍結。"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from PyQt5.QtCore import QThread, pyqtSignal as Signal

from ..core.models import ResampleOptions
from ..core.recorder import load_recorder
from ..core.resample import resample
from ..core.xlsx_writer import write_xlsx


@dataclass
class ConvertJob:
    input_folder: Path
    output_path: Path
    interval_seconds: int
    start: datetime | None
    end: datetime | None
    selected_channels: list[int]
    show_blanks: bool
    include_events: bool


class ConvertWorker(QThread):
    progress = Signal(str)
    finished_ok = Signal(int, str)
    failed = Signal(str)

    def __init__(self, job: ConvertJob) -> None:
        super().__init__()
        self.job = job

    def run(self) -> None:
        try:
            self.progress.emit("正在解析…")
            data = load_recorder(self.job.input_folder)

            self.progress.emit("正在重採樣…")
            opts = ResampleOptions(
                interval_seconds=self.job.interval_seconds,
                start=self.job.start,
                end=self.job.end,
                selected_channels=self.job.selected_channels,
                show_blanks=self.job.show_blanks,
            )
            rows = resample(data.samples, opts)

            self.progress.emit("正在寫檔…")
            names = [data.channels[i].name for i in self.job.selected_channels]
            write_xlsx(
                self.job.output_path,
                rows=rows,
                channels=data.channels,
                events=data.events,
                selected_channel_names=names,
                include_events=self.job.include_events,
            )
            self.finished_ok.emit(len(rows), str(self.job.output_path))
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))
