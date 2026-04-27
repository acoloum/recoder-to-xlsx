"""逆向探索工具：給定檔案 + offset 範圍，多種解讀印出。

用法範例：
  python tools/explore.py <file> --dump 0 --length 256
  python tools/explore.py <file> --at 0x40 --at 0x60
  python tools/explore.py <file> --find-float 22.8
  python tools/explore.py <file> --find-string "AI1"
  python tools/explore.py <file> --find-string "斷線" --encoding big5
"""
from __future__ import annotations

import argparse
import struct
from pathlib import Path


def hexdump(data: bytes, base: int = 0, length: int = 256) -> None:
    """印出 hex dump，格式同 hexdump -C。"""
    for i in range(0, min(length, len(data)), 16):
        chunk = data[i : i + 16]
        hex_part = " ".join(f"{b:02X}" for b in chunk)
        ascii_part = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        print(f"{base+i:08X}  {hex_part:<48}  {ascii_part}")


def interpret(data: bytes, offset: int) -> None:
    """對指定 offset 印出多種型別解讀。"""
    print(f"\n=== offset 0x{offset:08X} ({offset}) ===")
    if offset + 1 <= len(data):
        print(f"  u8  = {data[offset]}")
    if offset + 2 <= len(data):
        print(f"  u16 = {struct.unpack_from('<H', data, offset)[0]}")
        print(f"  i16 = {struct.unpack_from('<h', data, offset)[0]}")
    if offset + 4 <= len(data):
        print(f"  u32 = {struct.unpack_from('<I', data, offset)[0]}")
        print(f"  i32 = {struct.unpack_from('<i', data, offset)[0]}")
        print(f"  f32 = {struct.unpack_from('<f', data, offset)[0]:.6f}")
    if offset + 8 <= len(data):
        print(f"  u64 = {struct.unpack_from('<Q', data, offset)[0]}")
        print(f"  f64 = {struct.unpack_from('<d', data, offset)[0]:.6f}")
        # Windows FILETIME：100ns 間隔從 1601-01-01 起算
        ft = struct.unpack_from('<Q', data, offset)[0]
        if 116444736000000000 < ft < 133000000000000000:
            from datetime import datetime, timedelta, timezone
            epoch = datetime(1601, 1, 1, tzinfo=timezone.utc)
            dt = epoch + timedelta(microseconds=ft // 10)
            print(f"  FILETIME = {dt.strftime('%Y-%m-%d %H:%M:%S.%f')} UTC")
        # Unix timestamp（秒）
        if offset + 4 <= len(data):
            ts = struct.unpack_from('<I', data, offset)[0]
            if 1000000000 < ts < 2000000000:
                from datetime import datetime, timezone
                print(f"  Unix32  = {datetime.fromtimestamp(ts, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC")
        # Unix timestamp ms
        if offset + 8 <= len(data):
            tsms = struct.unpack_from('<Q', data, offset)[0]
            if 1000000000000 < tsms < 2000000000000:
                from datetime import datetime, timezone
                print(f"  UnixMs  = {datetime.fromtimestamp(tsms / 1000, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S.%f')} UTC")


def find_float(data: bytes, target: float, tol: float = 0.01) -> list[int]:
    """找所有值接近 target 的 f32 位置。"""
    hits = []
    for i in range(0, len(data) - 3):
        v = struct.unpack_from("<f", data, i)[0]
        if abs(v - target) < tol:
            hits.append(i)
    return hits


def find_string(data: bytes, needle: str, encoding: str = "big5") -> list[int]:
    """找字串（指定編碼）的所有出現位置。"""
    try:
        raw = needle.encode(encoding)
    except LookupError:
        raw = needle.encode("utf-8")
    hits = []
    start = 0
    while True:
        i = data.find(raw, start)
        if i < 0:
            break
        hits.append(i)
        start = i + 1
    return hits


def main() -> None:
    ap = argparse.ArgumentParser(
        description="無紙紀錄器二進位檔逆向探索工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("file", type=Path, help="要分析的二進位檔")
    ap.add_argument("--dump", type=lambda x: int(x, 0), metavar="OFFSET",
                    help="hex dump 起始 offset（支援 0x 前綴）")
    ap.add_argument("--length", type=int, default=256, help="dump 長度（預設 256）")
    ap.add_argument("--at", type=lambda x: int(x, 0), action="append", default=[],
                    metavar="OFFSET", help="對指定 offset 做多種解讀（可多次）")
    ap.add_argument("--find-float", type=float, metavar="VAL",
                    help="搜尋接近指定值的 f32")
    ap.add_argument("--find-string", type=str, metavar="STR",
                    help="搜尋字串（指定 --encoding）")
    ap.add_argument("--encoding", default="big5",
                    help="find-string 的字串編碼（預設 big5）")
    ap.add_argument("--stride", type=int, metavar="N",
                    help="配合 --dump，每 N byte 標記一次（協助找 record size）")
    args = ap.parse_args()

    data = args.file.read_bytes()
    print(f"檔案：{args.file.name}，大小：{len(data)} byte ({len(data):#x})")

    if args.dump is not None:
        print()
        hexdump(data, base=args.dump, length=args.length)
        if args.stride:
            print(f"\n--- stride {args.stride} 標記（共 {(args.length // args.stride)} 段）---")
            for seg in range(args.length // args.stride):
                off = args.dump + seg * args.stride
                if off < len(data):
                    interpret(data, off)

    for off in args.at:
        interpret(data, off)

    if args.find_float is not None:
        hits = find_float(data, args.find_float)
        print(f"\n找 f32 ~= {args.find_float}：{len(hits)} 處")
        for h in hits[:30]:
            val = struct.unpack_from("<f", data, h)[0]
            print(f"  0x{h:08X} ({h:6d})  →  {val:.4f}")

    if args.find_string is not None:
        hits = find_string(data, args.find_string, args.encoding)
        print(f"\n找字串 {args.find_string!r} ({args.encoding})：{len(hits)} 處")
        for h in hits[:30]:
            print(f"  0x{h:08X} ({h:6d})")


if __name__ == "__main__":
    main()
