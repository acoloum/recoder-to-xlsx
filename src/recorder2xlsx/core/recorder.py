"""聚合所有 parser，產生 RecorderData。"""
from __future__ import annotations

from pathlib import Path

from ..format.alarm_log import parse_alarm_log
from ..format.data_log import Sample, parse_day
from ..format.errors import RecorderFormatError
from ..format.file_list import parse_file_list
from ..format.panel_cfg import parse_panel_cfg
from ..format.tag_cfg import parse_tag_cfg
from .models import RecorderData


def load_recorder(folder: Path) -> RecorderData:
    parse_file_list(folder / "FileList.ini")
    channels = parse_tag_cfg(folder / "TagCfg.bin")
    pen_to_ch = parse_panel_cfg(folder / "PanelCfg.bin")

    datalog_root = folder / "DataStore" / "BatchDataLog" / "DataLog"
    if not datalog_root.is_dir():
        raise RecorderFormatError(f"缺 {datalog_root}")

    samples: dict[int, list[Sample]] = {i: [] for i in range(len(channels))}
    for day_dir in sorted(datalog_root.iterdir()):
        if not day_dir.is_dir():
            continue
        for pen_idx, ch_idx in pen_to_ch.items():
            if ch_idx >= len(channels):
                continue
            samples[ch_idx].extend(parse_day(day_dir, channel=pen_idx))

    for ch_idx in samples:
        samples[ch_idx].sort(key=lambda s: s.timestamp)

    events = parse_alarm_log(
        folder / "DataStore" / "BatchAlarm" / "Alarm" / "Alarm.lst"
    )

    return RecorderData(channels=channels, samples=samples, events=events)
