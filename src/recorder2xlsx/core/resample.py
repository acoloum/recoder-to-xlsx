"""重採樣：策略 A1（取樣） + B2（就近 + 空白標記）。"""
from __future__ import annotations

from bisect import bisect_left
from datetime import datetime, timedelta

from ..format.data_log import Sample
from .models import ResampledRow, ResampleOptions


def resample(
    samples: dict[int, list[Sample]], opts: ResampleOptions
) -> list[ResampledRow]:
    selected = opts.selected_channels or sorted(samples.keys())

    start = opts.start
    end = opts.end
    if start is None or end is None:
        all_times = [s.timestamp for ch in selected for s in samples.get(ch, [])]
        if not all_times:
            return []
        start = start or min(all_times)
        end = end or max(all_times)

    first_ch = next((ch for ch in selected if len(samples.get(ch, [])) >= 2), None)
    if first_ch is None:
        original_interval = opts.interval_seconds
    else:
        s0, s1 = samples[first_ch][0], samples[first_ch][1]
        original_interval = max(1, int((s1.timestamp - s0.timestamp).total_seconds()))

    tolerance = timedelta(seconds=min(original_interval, opts.interval_seconds) / 2)

    # 每通道的 timestamp 清單只建一次，避免在每次 _pick 呼叫時重建
    ch_data = {ch: samples.get(ch, []) for ch in selected}
    ch_timestamps = {ch: [s.timestamp for s in ch_data[ch]] for ch in selected}

    rows: list[ResampledRow] = []
    step = timedelta(seconds=opts.interval_seconds)
    t = start
    while t <= end:
        row_values: list[str] = []
        any_data = False
        for ch in selected:
            value = _pick(ch_data[ch], ch_timestamps[ch], t, tolerance)
            if value is None:
                row_values.append("")
            else:
                row_values.append(value)
                any_data = True

        if any_data or opts.show_blanks:
            rows.append(ResampledRow(timestamp=t, values=row_values))
        t += step

    return rows


def _pick(
    samples: list[Sample],
    timestamps: list[datetime],
    target: datetime,
    tolerance: timedelta,
) -> str | None:
    """找最接近 target 的樣本；若距離 > tolerance 則回傳 None。"""
    if not samples:
        return None
    i = bisect_left(timestamps, target)
    candidates = []
    if i < len(samples):
        candidates.append(samples[i])
    if i > 0:
        candidates.append(samples[i - 1])
    nearest = min(candidates, key=lambda s: abs(s.timestamp - target))
    if abs(nearest.timestamp - target) > tolerance:
        return None
    if nearest.status != "ok":
        return nearest.status
    return f"{nearest.value:.1f}"
