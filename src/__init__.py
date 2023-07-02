
from configparser import ConfigParser
import logging
import os
from .telegram import get_chat_id
from .logger import Log

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

TELEGRAM_API_KEY = conf.get('TELEGRAM', 'TELEGRAM_API_KEY', fallback=None)
if TELEGRAM_API_KEY:
    TELEGRAM_CHAT_ID = conf.get('TELEGRAM', 'TELEGRAM_CHAT_ID', fallback=get_chat_id(TELEGRAM_API_KEY))

MYSQL_HOST = conf.get('MYSQL', 'MYSQL_HOST', fallback='127.0.0.1')
MYSQL_PORT = conf.getint('MYSQL', 'MYSQL_PORT', fallback=3306)
USERNAME = conf.get('MYSQL', 'USERNAME', fallback=None)
PASSWORD = conf.get('MYSQL', 'PASSWORD', fallback=None)
DATABASE = conf.get('MYSQL', 'DATABASE', fallback=None)

# 建立log資料夾
if not os.path.exists(LOG_PATH) and not LOG_DISABLE:
    os.makedirs(LOG_PATH)

if LOG_DISABLE:
    logging.disable()
