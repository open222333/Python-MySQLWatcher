# Python-MySQLWatcher

監控多台 MySQL 主從複製（Master-Slave）的 Slave 狀態，偵測到異常時透過 Telegram Bot 即時回報。

---

## 目錄

- [功能說明](#功能說明)
- [專案結構](#專案結構)
- [執行流程](#執行流程)
- [使用方法](#使用方法)
- [設定檔說明](#設定檔說明)
- [建議注意事項](#建議注意事項)

---

## 功能說明

1. **多台 Slave 同時監控** — 透過 `host.json` 設定多台主機，各自以獨立執行緒並行監控
2. **主從複製狀態偵測** — 執行 `SHOW SLAVE STATUS` 查詢，偵測 `Slave_IO_Running` 或 `Slave_SQL_Running` 非 `Yes` 時觸發告警
3. **Telegram 告警通知** — 偵測到異常時自動透過 Telegram Bot 發送告警訊息
4. **可調整監控間隔** — 透過命令列參數或設定檔指定檢查頻率
5. **Docker 部署支援** — 提供 `docker-compose.yml` 與 `Dockerfile` 方便容器化部署

---

## 專案結構

```
Python-MySQLWatcher/
├── main.py                 # 主程式入口
├── requirements.txt        # 相依套件
├── Dockerfile              # Docker 映像建置檔
├── docker-compose.yml      # Docker 部署設定
├── conf/
│   ├── config.ini.default  # 設定檔範本
│   └── host.json.default   # 主機清單範本
├── logs/                   # 日誌輸出目錄
└── src/
    ├── __init__.py         # 讀取設定（LOG_LEVEL、HOSTS、MONITORING_INTERVAL 等）
    ├── logger.py           # 日誌模組
    └── mysql.py            # MySQLStatusWatcher、MySQLClusterWatch 監控核心
```

---

## 執行流程

```
執行 main.py
    |
    +--> 解析命令列參數（-s SLEEP_SEC、-t TYPE、-l LOG_LEVEL）
    |
    +--> 讀取 conf/config.ini（Telegram 設定、監控間隔、host.json 路徑）
    |
    +--> 讀取 conf/host.json（主機清單）
    |
    +--> 遍歷主機清單，每台主機建立獨立執行緒
            |
            +--> 建立 MySQLStatusWatcher（master_slave 模式）
            |    或 MySQLClusterWatch（cluster 模式）
            |
            +--> watcher.run() 進入監控迴圈
                    |
                    +--> 連線至 MySQL，執行 SHOW SLAVE STATUS
                    |
                    +--> 檢查 Slave_IO_Running == 'Yes'？
                    |       +--> 否 --> 透過 Telegram Bot 發送告警
                    |
                    +--> 檢查 Slave_SQL_Running == 'Yes'？
                    |       +--> 否 --> 透過 Telegram Bot 發送告警
                    |
                    +--> 等待 MONITORING_INTERVAL 秒後重複執行
```

---

## 使用方法

### 1. 安裝相依套件

```bash
pip install -r requirements.txt
```

### 2. 複製設定檔

```bash
cp conf/config.ini.default conf/config.ini
cp conf/host.json.default conf/host.json
```

### 3. 設定 Telegram Bot

編輯 `conf/config.ini`，填入 Telegram API Key 與 Chat ID：

```ini
[TELEGRAM]
TELEGRAM_API_KEY=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

### 4. 設定監控主機清單

編輯 `conf/host.json`，填入各台 MySQL Slave 主機資訊：

```json
[
  {
    "hostname": "db-slave-1",
    "ip": "192.168.1.101",
    "port": 3306,
    "username": "monitor_user",
    "password": "your_password",
    "database": "mysql"
  }
]
```

### 5. 執行監控

```bash
# 使用預設設定執行
python main.py

# 指定監控間隔為 30 秒
python main.py -s 30

# 指定 log 等級為 DEBUG
python main.py -l DEBUG

# 組合使用
python main.py -s 30 -l INFO
```

### 6. 使用 Docker 執行

```bash
# 背景執行
docker compose up -d

# 查看日誌
docker compose logs -f
```

### 命令列參數說明

```
usage: main.py [-h] [-s SLEEP_SEC] [-t {master_slave,cluster}] [-l {DEBUG,INFO,WARNING,ERROR,CRITICAL}]

options:
  -h, --help            顯示說明並離開
  -s SLEEP_SEC, --sleep_sec SLEEP_SEC
                        設定監控間隔時間（秒）
  -t {master_slave,cluster}, --type {master_slave,cluster}
                        監控模式，預設 master_slave
  -l {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --log_level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        設定 log 等級，預設 WARNING
```

---

## 設定檔說明

### conf/config.ini

```ini
[LOG]
; 關閉 log 功能，輸入 true / 1，預設不關閉
; LOG_DISABLE=

; log 檔案輸出路徑，預設 logs/
; LOG_PATH=

; 關閉輸出 log 檔案，輸入 true / 1，預設關閉（不輸出檔案）
; LOG_FILE_DISABLE=1

; log 等級：DEBUG / INFO / WARNING / ERROR / CRITICAL，預設 WARNING
; LOG_LEVEL=

[TELEGRAM]
; Telegram Bot Token
; TELEGRAM_API_KEY=

; Telegram 接收告警的 Chat ID
; TELEGRAM_CHAT_ID=

[HOST_SETTING]
; 主機清單 JSON 檔路徑，預設 conf/host.json
; HOST_JSON_PATH=

; 監控間隔秒數，預設 10
; MONITORING_INTERVAL=
```

### conf/host.json

```json
[
  {
    "hostname": "sample-1",
    "ip": "127.0.0.1",
    "port": 3306,
    "username": "root",
    "password": "password",
    "database": "mysql"
  }
]
```

| 欄位      | 型別    | 說明                                |
|---------|---------|-------------------------------------|
| hostname | string | 主機識別名稱（用於告警訊息顯示）    |
| ip       | string | MySQL 主機 IP 位址                  |
| port     | integer | 連接埠，預設 3306                   |
| username | string | MySQL 使用者名稱                    |
| password | string | MySQL 密碼                          |
| database | string | 連線使用的資料庫，通常填 `mysql`    |

---

## 建議注意事項

- **帳號權限** — 監控帳號需具備 `REPLICATION CLIENT` 權限才能執行 `SHOW SLAVE STATUS`，建議建立專屬監控帳號，避免使用 root
- **Telegram 設定** — 若未設定 `TELEGRAM_API_KEY` 與 `TELEGRAM_CHAT_ID`，告警訊息只會寫入 log，不會傳送通知
- **監控間隔** — 命令列參數 `-s` 的優先級高於 `config.ini` 的 `MONITORING_INTERVAL`
- **密碼安全** — `host.json` 含有明文密碼，請限制檔案讀取權限（`chmod 600`），切勿提交至版本控制
- **Docker 時區** — 容器內預設時區可能與主機不同，若告警訊息時間顯示有誤，請在 `docker-compose.yml` 中設定 `TZ` 環境變數
- **監控程式本身的穩定性** — 建議以 Docker restart policy（`restart: always`）或 systemd 確保監控程式本身不會中斷
- **多台主機** — 每台主機以獨立執行緒運作，主機數量增加不影響各自的監控間隔準確性
