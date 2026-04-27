"""重採樣測試（合成資料）。"""
from datetime import datetime, timedelta

from recorder2xlsx.core.models import ResampleOptions
from recorder2xlsx.core.resample import resample
from recorder2xlsx.format.data_log import Sample


def _make(ts: datetime, val: float, status: str = "ok") -> Sample:
    return Sample(timestamp=ts, value=val, status=status)


def test_a1_exact_match():
    """間隔等於原始 → 全部取出。"""
    base = datetime(2026, 4, 24, 0, 0, 0)
    samples = {0: [_make(base + timedelta(seconds=120 * i), float(i)) for i in range(5)]}
    rows = resample(samples=samples, opts=ResampleOptions(interval_seconds=120, selected_channels=[0]))
    assert len(rows) == 5
    assert rows[0].values == ["0.0"]
    assert rows[4].values == ["4.0"]


def test_a1_downsample():
    """原始 60 秒、要 120 秒 → 取每隔一筆。"""
    base = datetime(2026, 4, 24, 0, 0, 0)
    samples = {0: [_make(base + timedelta(seconds=60 * i), float(i)) for i in range(10)]}
    rows = resample(samples=samples, opts=ResampleOptions(interval_seconds=120, selected_channels=[0]))
    assert len(rows) == 5
    assert rows[0].values == ["0.0"]
    assert rows[1].values == ["2.0"]


def test_b2_upsample_with_blanks():
    """原始 120 秒、要 60 秒、show_blanks=True → 一半空白。"""
    base = datetime(2026, 4, 24, 0, 0, 0)
    samples = {0: [_make(base + timedelta(seconds=120 * i), float(i)) for i in range(3)]}
    rows = resample(
        samples=samples,
        opts=ResampleOptions(interval_seconds=60, selected_channels=[0], show_blanks=True),
    )
    assert [r.values[0] for r in rows] == ["0.0", "", "1.0", "", "2.0"]


def test_b2_upsample_skip_blanks():
    """原始 120 秒、要 60 秒、show_blanks=False → 跳過空白。"""
    base = datetime(2026, 4, 24, 0, 0, 0)
    samples = {0: [_make(base + timedelta(seconds=120 * i), float(i)) for i in range(3)]}
    rows = resample(
        samples=samples,
        opts=ResampleOptions(interval_seconds=60, selected_channels=[0], show_blanks=False),
    )
    assert [r.values[0] for r in rows] == ["0.0", "1.0", "2.0"]


def test_status_passthrough():
    """斷線狀態應顯示中文，不顯示數值。"""
    base = datetime(2026, 4, 24, 0, 0, 0)
    samples = {0: [_make(base, 99.0, status="斷線")]}
    rows = resample(samples=samples, opts=ResampleOptions(interval_seconds=120, selected_channels=[0]))
    assert rows[0].values == ["斷線"]


def test_time_range_filter():
    base = datetime(2026, 4, 24, 0, 0, 0)
    samples = {0: [_make(base + timedelta(seconds=120 * i), float(i)) for i in range(5)]}
    rows = resample(
        samples=samples,
        opts=ResampleOptions(
            interval_seconds=120,
            selected_channels=[0],
            start=base + timedelta(seconds=120),
            end=base + timedelta(seconds=360),
        ),
    )
    assert [r.values[0] for r in rows] == ["1.0", "2.0", "3.0"]


def test_multi_channel():
    base = datetime(2026, 4, 24, 0, 0, 0)
    samples = {
        0: [_make(base, 1.0)],
        1: [_make(base, 2.0)],
        2: [_make(base, 3.0)],
    }
    rows = resample(
        samples=samples,
        opts=ResampleOptions(interval_seconds=120, selected_channels=[0, 2]),
    )
    assert rows[0].values == ["1.0", "3.0"]
