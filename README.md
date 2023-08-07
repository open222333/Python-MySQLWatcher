# Python-MySQLWatcher

```
監控 MySQL
```

## 目前功能

1. 監控 主從的 Slave 狀態 (可同時監控多台)
2. 回報至 Telegram (需設置 TELEGRAM_API_KEY, TELEGRAM_CHAT_ID)

## 配置文檔

```bash
# 複製預設配置文檔
cp .conf/config.ini.default .conf/config.ini
cp .conf/host.json.default .conf/host.json
```

### config.ini

```ini
[LOG]
; ******log設定******
; 關閉log功能 輸入選項 (true, True, 1) 預設 不關閉
; LOG_DISABLE=1

; logs路徑 預設 logs
; LOG_PATH=

; 關閉紀錄log檔案 輸入選項 (true, True, 1)  預設 關閉
; LOG_FILE_DISABLE=1

; 設定紀錄log等級 DEBUG,INFO,WARNING,ERROR,CRITICAL 預設WARNING
; LOG_LEVEL=

[TELEGRAM]
; 設置 Telegram 相關參數
; TELEGRAM_API_KEY=
; TELEGRAM_CHAT_ID=

[HOST_SETTING]
; 主機相關設定json檔路徑 預設 .conf/host.json
; HOST_JSON_PATH=
```

### host.json

```json
[
  {
    "hostname": "sample-1",
    "ip": "127.0.0.1",
    "port": 3306,
    "username": "root",
    "password": "password",
    "database": "mysql"
  },
  {
    "hostname": "sample-2",
    "ip": "192.168.0.1",
    "port": 3306,
    "username": "root",
    "password": "password",
    "database": "mysql"
  }
]
```

## 執行方式

### cmd bash 執行指令

```bash
python main.py
```

```
usage: main.py [-h] [-s SLEEP_SEC] [-l {DEBUG,INFO,WARNING,ERROR,CRITICAL}]

options:
  -h, --help            show this help message and exit
  -s SLEEP_SEC, --sleep_sec SLEEP_SEC
                        設定間隔時間
  -l {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --log_level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        設定紀錄log等級 DEBUG,INFO,WARNING,ERROR,CRITICAL 預設WARNING
```

### docker-compose執行

```bash
docker-compose up -d
```
