# Python-MySQLWatcher

監控多台 MySQL 主從複製（Master-Slave）的 Slave 狀態，偵測到異常時透過 Telegram Bot 即時回報。

---

## 目錄

- [功能說明](#功能說明)
- [專案結構](#專案結構)
- [執行流程](#執行流程)
- [使用方法](#使用方法)
- [設定檔說明](#設定檔說明)
- [背景執行（不使用-docker）](#背景執行不使用-docker)
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
    ├── mysql.py            # MySQLStatusWatcher、MySQLClusterWatch 監控核心
    ├── telegram.py         # Telegram Bot 通知模組
    └── tool.py             # 工具函式（時間格式等）
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
                    +--> 執行 SELECT VERSION() 取得版本（快取，只查一次）
                    |
                    +--> 版本 >= 8.4？
                    |       +--> 是 --> SHOW REPLICA STATUS（Replica_IO_Running / Replica_SQL_Running）
                    |       +--> 否 --> SHOW SLAVE STATUS（Slave_IO_Running / Slave_SQL_Running）
                    |
                    +--> 檢查 IO_Running == 'Yes'？
                    |       +--> 否 --> 透過 Telegram Bot 發送告警
                    |
                    +--> 檢查 SQL_Running == 'Yes'？
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

## 背景執行（不使用 Docker）

### nohup（快速啟動）

```bash
# 背景執行，log 輸出至 nohup.out
nohup python main.py -s 30 &

# 背景執行，指定 log 導向自訂檔案
nohup python main.py -s 30 >> logs/nohup.log 2>&1 &

# 查看 PID
echo $!

# 停止
kill <PID>
```

### systemd（伺服器長期運行）

建立服務設定檔 `/etc/systemd/system/mysql-watcher.service`：

```ini
[Unit]
Description=MySQL Watcher
After=network.target

[Service]
Type=simple
User=<執行使用者>
WorkingDirectory=<專案絕對路徑>
ExecStart=python main.py -s 30
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# 重新載入設定
sudo systemctl daemon-reload

# 啟用開機自動啟動
sudo systemctl enable mysql-watcher

# 啟動服務
sudo systemctl start mysql-watcher

# 查看狀態
sudo systemctl status mysql-watcher

# 查看即時 log
sudo journalctl -u mysql-watcher -f

# 停止服務
sudo systemctl stop mysql-watcher
```

---

## 建議注意事項

- **帳號權限** — 監控帳號需具備 `REPLICATION CLIENT` 權限才能執行 `SHOW SLAVE STATUS`，建議建立專屬監控帳號，避免使用 root
- **Telegram 設定** — 若未設定 `TELEGRAM_API_KEY` 與 `TELEGRAM_CHAT_ID`，告警訊息只會寫入 log，不會傳送通知
- **監控間隔** — 命令列參數 `-s` 的優先級高於 `config.ini` 的 `MONITORING_INTERVAL`
- **密碼安全** — `host.json` 含有明文密碼，請限制檔案讀取權限（`chmod 600`），切勿提交至版本控制
- **Docker 時區** — 容器內預設時區可能與主機不同，若告警訊息時間顯示有誤，請在 `docker-compose.yml` 中設定 `TZ` 環境變數
- **監控程式本身的穩定性** — 建議以 Docker restart policy（`restart: always`）或 systemd 確保監控程式本身不會中斷
- **多台主機** — 每台主機以獨立執行緒運作，主機數量增加不影響各自的監控間隔準確性

---

## 疑難排解：為什麼會收到「MySQL replica同步異常」告警？

`SHOW REPLICA/SLAVE STATUS` 查詢失敗（回傳 None）就會觸發此告警，可能原因包含（依常見程度排序）：

1. **監控端 → DB 的網路層問題**：TCP 逾時、封包遺失、跨機房/跨境連線抖動、防火牆或安全群組規則變動、DNS 暫時解析失敗。
2. **MySQL 連線資源問題**：`max_connections` 滿載、帳號因連續連線錯誤被暫時封鎖（需 `FLUSH HOSTS`）、監控帳號密碼過期或權限被異動。
3. **MySQL 服務瞬斷**：套件更新／OOM Killer／資源不足造成 `mysqld` 重啟，或當時 CPU/IO 過載導致查詢逾時。
4. **Replication 執行緒真的短暫中斷**：Master 端執行備份（`mysqldump`/`xtrabackup`）造成的鎖表、binlog rotate/purge、網路分斷造成 IO thread 重新連線。
5. **監控程式本身的邏輯限制（已於本次優化修正，詳見下方）**：例外訊息未帶入告警內容、MySQL 版本快取失敗會被永久卡住、單一例外會讓該主機監控執行緒永久停止、單次瞬斷就會發送告警。

若再次收到告警，可先查看監控程式的 log（`logs/` 目錄或 `docker compose logs -f`）取得詳細錯誤原因，再視情況檢查該台 MySQL 主機的 error log 與網路狀況。

### 本次優化內容（`src/mysql.py`）

- **告警內容加入實際錯誤原因**：查詢失敗時，Telegram 訊息會附上錯誤代碼/訊息，不再只顯示籠統的「同步異常」，方便事後追查。
- **修正版本偵測快取陷阱**：原本第一次查詢 MySQL 版本若剛好連線失敗，會把 fallback 版本 `(0,0,0)` 永久快取，導致往後持續誤用錯誤指令。改為優先嘗試 `SHOW REPLICA STATUS`、失敗時自動 fallback `SHOW SLAVE STATUS`（並在下次查詢時自動重新偵測），不再依賴額外的版本查詢。
- **加入延遲秒數與最後錯誤訊息**：若該版本有回傳 `Seconds_Behind_Master`/`Last_IO_Error`/`Last_SQL_Error`，會一併顯示在告警訊息中，避免只看到 `IO/SQL Running: Yes` 卻不知道實際延遲多久、上次錯誤是什麼。
- **告警防抖（debounce）**：新增 `ANOMALY_THRESHOLD`（預設 2 次），需連續偵測到異常達門檻才會發送告警，避免單次網路瞬斷造成誤報與告警疲勞；改為 1 可還原成原本「偵測到一次就告警」的行為。
- **監控執行緒不再因單一例外永久停止**：原本 `run()` 內未預期的例外會 `break` 離開迴圈，導致該主機從此不再被監控（且不會有任何提示）。修正為記錄錯誤後於下一輪繼續監控。
- **連線加上逾時設定**：`connect_timeout`/`read_timeout`/`write_timeout` 預設 5 秒，避免 DB 無回應時監控執行緒被無限期卡住。
- **修正 Cluster 模式（`MySQLClusterWatch`）的既有錯誤**：原本呼叫 `connection.is_connected()`（不存在於 `MysqlConnect`/PyMySQL）與 `cursor(dictionary=True)`（`mysql-connector-python` API，非 PyMySQL 語法），實際執行必定拋例外，已改用與 `MySQLStatusWatcher` 一致的連線方式修正。
