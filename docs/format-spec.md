# 祿將 DR2018 檔案格式（逆向）

> 範例檔來源：`../範例/無紙記錄器檔案/`
> 對照輸出：`../範例/輸出檔案/042726141613_Pen.csv`

## 1. FileList.ini
INI 文字檔，UTF-8。`[General].Instrument=PR`、`Ver=242`。

## 2. Alarm.lst

已確認（2026-04-27 逆向）。

### 檔案結構
```
[Header 20 bytes]
[Record 0][Record 1]...[Record N-1]  # 每筆 304 bytes
```

### Header（20 bytes）
| Offset | Size | Type   | 說明                  |
|--------|------|--------|-----------------------|
| 0x00   | 4    | u32 LE | 固定 0x00000000       |
| 0x04   | 2    | u16 LE | 固定 0x03E8（1000）   |
| 0x06   | 2    | u16 LE | record size = 0x0130（304） |
| 0x08   | 2    | u16 LE | record count（本例 203）    |
| 0x0A   | 10   | bytes  | 補零                  |

### Record（304 bytes）
| Offset | Size | Type    | 說明                        |
|--------|------|---------|-----------------------------|
| 0x00   | 4    | u32 LE  | 固定 0x00000000             |
| 0x04   | 4    | u32 LE  | 固定 0x00000000             |
| 0x08   | 8    | u64 LE  | **發生時間 FILETIME（UTC）** |
| 0x10   | 288  | bytes   | 依事件類型而定（系統事件均為零） |

> FILETIME：Windows 100 ns ticks since 1601-01-01 00:00:00 UTC（u64 LE）。
> 使用方式：`epoch + timedelta(microseconds=ft // 10)`，其中 epoch = `datetime(1601,1,1,tzinfo=utc)`。

### Action Type（byte[3]）
byte[3]（即 offset 0x03，u8）決定事件動作：

| 值   | 動作       |
|------|-----------|
| 0x06 | 開機       |
| 0x07 | 更新       |
| 0x0F | 卸載       |
| 0x10 | 開機（初始）|
| 其他  | 未知，保留原始 hex 值 |

### 各欄輸出對應
- 確認：固定空白
- 動作：依上表映射
- 來源：固定空白（系統事件無通道；如未來有警報事件型別再擴充）
- 發生時間：FILETIME at 0x08（轉 `yyyy-mm-dd HH:MM:SS` UTC）
- 清除時間：固定空白（目前樣本均無）
- 數值/內容：固定空白

---

## 3. TagCfg.bin

已確認（2026-04-27 逆向）。

### 檔案概要
- 大小：692032 bytes（範例）
- 通道記錄從 offset **0xDE56**（56918）開始
- Stride（記錄間距）：**1384 bytes**（0x568）
- 共 18 通道（AI1~AI18，index 0~17）

### 通道記錄欄位（相對 record 起點）
| 偏移   | Size | Type      | 說明                  |
|--------|------|-----------|-----------------------|
| 0x000  | ≤64  | UTF-16-LE | 通道名稱（null-terminated）|
| 0x082  | 8    | f64 LE    | 量測下限（range_low）  |
| 0x08A  | 8    | f64 LE    | 量測上限（range_high） |
| 0x2DE  | ≤32  | UTF-16-LE | 工程單位（unit，null-terminated）|

> 字串讀法：讀出 raw bytes，找第一個 u16 = 0x0000 截斷，再 `bytes.decode('utf-16-le')`。

### 通道 N（0-indexed）起始 offset
```
offset = 0xDE56 + N * 0x568
```

---

## 4. Pn.idx + Pn.dat

已確認（2026-04-27 逆向）。

### Pn.dat（通道 N 原始資料）
- 無 header
- 每個 sample = 2 bytes，u16 LE，packed 緊密排列
- 採樣率：1 sample/秒
- 值：`raw / 10.0` = 工程值（°C 等）
- 特殊值：`0x7FFF (32767)` = 斷線（"斷線"）

### Pn.idx（索引）
格式：64-byte header（含首筆 entry），後接可變數量的 32-byte entries。

**Header（64 bytes）**
| Offset | Size | 說明                            |
|--------|------|---------------------------------|
| 0x00   | 32   | 未知 header 欄位                |
| 0x20   | 8    | 首筆 entry FILETIME（UTC）      |
| 0x28   | 4    | 首筆 entry 對應 dat byte offset |
| 0x2C   | 4    | 首筆 entry 樣本數 count         |
| 0x30   | 16   | 首筆 entry 其餘未知欄位          |

**後續 Entry（每筆 32 bytes，從 offset 0x40 開始）**
| 偏移   | Size | 說明                  |
|--------|------|-----------------------|
| 0x00   | 8    | FILETIME（UTC）        |
| 0x08   | 4    | 對應 dat byte offset   |
| 0x0C   | 4    | 樣本數 count           |
| 0x10   | 16   | 未知欄位               |

### 使用方式
1. 讀取首筆 entry 的 FILETIME（`t0`）與 dat_byte_offset
2. 目標時間 `T` 的 sample index = `(T - t0).total_seconds()`（四捨五入為整數）
3. dat 中的值 = `u16_le_at(dat, (dat_byte_offset + sample_index * 2))`
4. idx 的後續 entry 用於大型 dat 快速 seek（本程式順序讀全部，不需要 seek）

---

## 5. PanelCfg.bin
TBD（Task 8 填寫）。預設：Pen N → AI(N+1)（N 從 0 開始）。
