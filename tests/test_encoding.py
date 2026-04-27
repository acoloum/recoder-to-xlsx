"""Big5 解碼輔助測試。"""
from recorder2xlsx.format.encoding import decode_big5_z


def test_decode_ascii():
    """純 ASCII 字串正確解碼。"""
    assert decode_big5_z(b"AI1\x00\x00") == "AI1"


def test_decode_zero_terminator():
    """遇到 \x00 截斷。"""
    raw = "通道".encode("big5") + b"\x00\x00\xff\xff"
    assert decode_big5_z(raw) == "通道"


def test_decode_chinese():
    """中文字串（斷線）正確解碼。"""
    raw = "斷線".encode("big5") + b"\x00"
    assert decode_big5_z(raw) == "斷線"


def test_decode_invalid_replace():
    """無效 bytes 用 replace 模式不拋錯。"""
    result = decode_big5_z(b"\xff\xfe\xfd", errors="replace")
    assert isinstance(result, str)
