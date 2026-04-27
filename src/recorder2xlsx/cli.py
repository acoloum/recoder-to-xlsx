"""命令列入口。"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

from .core.models import ResampleOptions
from .core.recorder import load_recorder
from .core.resample import resample
from .core.xlsx_writer import write_xlsx


def _parse_dt(s: str) -> datetime:
    return datetime.fromisoformat(s)


def run_cli(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="recorder2xlsx-cli")
    ap.add_argument("input_folder", type=Path)
    ap.add_argument("-o", "--output", type=Path, required=True)
    ap.add_argument("--interval", type=int, default=120)
    ap.add_argument("--start", type=_parse_dt)
    ap.add_argument("--end", type=_parse_dt)
    ap.add_argument("--channels", help="逗號分隔的 1-based AI 索引，如 1,2,5")
    ap.add_argument("--no-blanks", action="store_true")
    ap.add_argument("--no-events", action="store_true")
    args = ap.parse_args(argv)

    data = load_recorder(args.input_folder)

    if args.channels:
        selected = [int(x) - 1 for x in args.channels.split(",")]
    else:
        selected = list(range(len(data.channels)))

    opts = ResampleOptions(
        interval_seconds=args.interval,
        start=args.start,
        end=args.end,
        selected_channels=selected,
        show_blanks=not args.no_blanks,
    )
    rows = resample(data.samples, opts)

    selected_names = [data.channels[i].name for i in selected]
    write_xlsx(
        args.output,
        rows=rows,
        channels=data.channels,
        events=data.events,
        selected_channel_names=selected_names,
        include_events=not args.no_events,
    )
    print(f"完成，共 {len(rows)} 筆，輸出於 {args.output}")
    return 0


def main() -> None:
    sys.exit(run_cli(sys.argv[1:]))
