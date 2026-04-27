# recorder2xlsx

祿將 DR2018 無紙紀錄器資料夾轉 `.xlsx` 工具（Linux / Zorin OS 18）。

## 安裝（Linux）

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## 使用

GUI：

```bash
recorder2xlsx
```

CLI：

```bash
recorder2xlsx-cli <輸入資料夾> -o output.xlsx --interval 120
```

## 開發

```bash
pytest
```

## 已知限制
- 目前只支援 Instrument=PR（祿將 DR2018）。VR06 / VR18 / HMI 未驗證。
- 資料間隔 < 原始紀錄間隔時，會以「就近樣本」填補。
- 多日資料統一在同一張「資料」分頁，跨日連續排列。

## 開發備忘
- 二進位格式逆向結果見 `docs/format-spec.md`。
- 範例資料與預期輸出在專案父目錄 `範例/`。
