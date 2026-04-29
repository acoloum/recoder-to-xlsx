"""聚合所有 parser，產生 RecorderData。"""
from __future__ import annotations

from collections.abc import Callable
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


def load_recorder(
    folder: Path,
    progress_cb: "Callable[[str], None] | None" = None,
) -> RecorderData:
    """載入整個紀錄器資料夾。

    Args:
        folder: 紀錄器根目錄。
        progress_cb: 可選的進度回呼，接受一個說明字串，在背景執行緒中呼叫。
    """
    def _report(msg: str) -> None:
        if progress_cb is not None:
            progress_cb(msg)

    _report("讀取設定檔…")
    parse_file_list(folder / "FileList.ini")
    channels = parse_tag_cfg(folder / "TagCfg.bin")
    pen_to_ch = parse_panel_cfg(folder / "PanelCfg.bin")

    datalog_root = folder / "DataStore" / "BatchDataLog" / "DataLog"
    if not datalog_root.is_dir():
        raise RecorderFormatError(f"缺 {datalog_root}")

    day_dirs = sorted(d for d in datalog_root.iterdir() if d.is_dir())
    valid_pens = [(pen_idx, ch_idx) for pen_idx, ch_idx in pen_to_ch.items() if ch_idx < len(channels)]
    total_days = len(day_dirs)

    samples: dict[int, list[Sample]] = {i: [] for i in range(len(channels))}

    # 以執行緒平行解析所有（日期 × 通道）組合，每完成一天更新進度
    tasks = [(day_dir, pen_idx, ch_idx) for day_dir in day_dirs for pen_idx, ch_idx in valid_pens]
    total_tasks = len(tasks)
    done_count = 0
    # 追蹤每個 future 對應的日期名稱，用來計算已完成天數
    day_done: dict[str, int] = {}  # day_name → 已完成的 pen 數量
    pens_per_day = len(valid_pens) if valid_pens else 1

    with ThreadPoolExecutor() as executor:
        future_to_day = {
            executor.submit(_load_day_channel, day_dir, pen_idx, ch_idx): day_dir.name
            for day_dir, pen_idx, ch_idx in tasks
        }
        for future in as_completed(future_to_day):
            ch_idx, day_samples = future.result()
            samples[ch_idx].extend(day_samples)

            day_name = future_to_day[future]
            day_done[day_name] = day_done.get(day_name, 0) + 1
            days_finished = sum(1 for v in day_done.values() if v >= pens_per_day)
            done_count += 1
            _report(f"讀取資料中… 第 {days_finished}/{total_days} 天（{done_count}/{total_tasks} 筆）")

    _report("排序中…")
    for ch_idx in samples:
        samples[ch_idx].sort(key=lambda s: s.timestamp)

    _report("讀取事件記錄…")
    events = parse_alarm_log(
        folder / "DataStore" / "BatchAlarm" / "Alarm" / "Alarm.lst"
    )

    return RecorderData(channels=channels, samples=samples, events=events)
