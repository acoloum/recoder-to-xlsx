"""Big5 字串解碼輔助。"""
from __future__ import annotations


def decode_big5_z(raw: bytes, *, errors: str = "replace") -> str:
    """解碼 Big5（cp950）字串，遇到 \\x00 截斷。

    無紙紀錄器內字串多為定長欄位填 0，需手動截斷。

    Parameters
    ----------
    raw:
        原始位元組資料。
    errors:
        解碼錯誤處理模式，預設為 "replace"。
        可傳入 "strict"、"ignore"、"replace" 等標準模式。

    Returns
    -------
    str
        截斷並解碼後的字串。
    """
    # 找到第一個 null 終止符，截斷其後的資料
    end = raw.find(b"\x00")
    if end >= 0:
        raw = raw[:end]
    return raw.decode("big5", errors=errors)
