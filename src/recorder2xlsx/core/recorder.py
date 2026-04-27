"""聚合所有 parser，產生 RecorderData。"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from ..format.alarm_log import parse_alarm_log
from ..format.data_log import Sample, parse_day
from ..format.errors import RecorderFormatError
from ..format.file_list import parse_file_list
from ..format.panel_cfg import parse_panel_cfg
from ..format.tag_cfg import parse_tag_cfg
from .models import RecorderData


def _load_day_channel(day_dir: Path, pen_idx: int, ch_idx: int) -> tuple[int, list[Sample]]:
    """載入單一（日期目錄 × 通道）的 samples，供平行執行。"""
    try:
        return ch_idx, parse_day(day_dir, channel=pen_idx)
    except Exception:
        return ch_idx, []


def load_recorder(folder: Path) -> RecorderData:
    parse_file_list(folder / "FileList.ini")
    channels = parse_tag_cfg(folder / "TagCfg.bin")
    pen_to_ch = parse_panel_cfg(folder / "PanelCfg.bin")

    datalog_root = folder / "DataStore" / "BatchDataLog" / "DataLog"
    if not datalog_root.is_dir():
        raise RecorderFormatError(f"缺 {datalog_root}")

    day_dirs = sorted(d for d in datalog_root.iterdir() if d.is_dir())
    valid_pens = [(pen_idx, ch_idx) for pen_idx, ch_idx in pen_to_ch.items() if ch_idx < len(channels)]

    samples: dict[int, list[Sample]] = {i: [] for i in range(len(channels))}

    # 以執行緒平行解析所有（日期 × 通道）組合
    tasks = [(day_dir, pen_idx, ch_idx) for day_dir in day_dirs for pen_idx, ch_idx in valid_pens]
    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(_load_day_channel, day_dir, pen_idx, ch_idx): ch_idx
                   for day_dir, pen_idx, ch_idx in tasks}
        for future in as_completed(futures):
            ch_idx, day_samples = future.result()
            samples[ch_idx].extend(day_samples)

    for ch_idx in samples:
        samples[ch_idx].sort(key=lambda s: s.timestamp)

    events = parse_alarm_log(
        folder / "DataStore" / "BatchAlarm" / "Alarm" / "Alarm.lst"
    )

    return RecorderData(channels=channels, samples=samples, events=events)
