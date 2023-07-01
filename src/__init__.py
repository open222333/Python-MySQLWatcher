from configparser import ConfigParser

conf = ConfigParser()
conf.read('.conf/config.ini', encoding='utf-8')


# logs相關參數
# 關閉log功能 輸入選項 (true, True, 1) 預設 不關閉
LOG_DISABLE = conf.getboolean('LOG', 'LOG_DISABLE', fallback=False)
# logs路徑 預設 logs
LOG_PATH = conf.get('LOG', 'LOG_PATH', fallback='logs')
# 設定紀錄log等級 DEBUG,INFO,WARNING,ERROR,CRITICAL 預設WARNING
LOG_LEVEL = conf.get('LOG', 'LOG_LEVEL', fallback='WARNING')
# 關閉紀錄log檔案 輸入選項 (true, True, 1)  預設 不關閉
LOG_FILE_DISABLE = conf.getboolean('LOG', 'LOG_FILE_DISABLE', fallback=False)
# 指定log大小(輸入數字) 單位byte, 與 LOG_DAYS 只能輸入一項 若都輸入 LOG_SIZE優先
LOG_SIZE = conf.getint('LOG', 'LOG_SIZE', fallback=0)
# 指定保留log天數(輸入數字) 預設7
LOG_DAYS = conf.getint('LOG', 'LOG_DAYS', fallback=7)

TELEGRAM_API_KEY = conf.get('TELEGRAM', 'TELEGRAM_API_KEY', fallback=None)
TELEGRAM_CHAT_ID = conf.get('TELEGRAM', 'TELEGRAM_CHAT_ID', fallback=None)

MYSQL_HOST=conf.get('MYSQL', 'MYSQL_HOST', fallback='127.0.0.1')
MYSQL_PORT=conf.getint('MYSQL', 'MYSQL_PORT', fallback=3306)
USERNAME=conf.get('MYSQL', 'USERNAME', fallback=None)
PASSWORD=conf.get('MYSQL', 'PASSWORD', fallback=None)
DATABASE=conf.get('MYSQL', 'DATABASE', fallback=None)