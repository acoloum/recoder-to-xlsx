"""PanelCfg.bin Pen↔AI 通道對應（最低限度 stub）。

目前範例的 18 個 Pen 依序對應 AI1~AI18；二進位格式尚未完整逆向，
若未來遇到 Pen 順序不同的紀錄器，再回頭補真實解析。
"""
from __future__ import annotations

from pathlib import Path

from .errors import RecorderFormatError


def parse_panel_cfg(path: Path) -> dict[int, int]:
    """回傳 {pen_index: channel_index}（兩者均 0-based）。"""
    if not path.is_file():
        raise RecorderFormatError(f"找不到 {path}")
    return {i: i for i in range(18)}
