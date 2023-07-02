import socket
import pymysql
import requests
from time import sleep
from typing import Union
from .logger import Log
from . import LOG_LEVEL

logger = Log()
logger.set_level(LOG_LEVEL)
logger.set_msg_handler()


class MySQLStatusWatcher():

    def __init__(self, user: str, password: str, database: str, host: str = '127.0.0.1', port: int = 3306) -> None:
        """mysql 狀態 監控程式

        Args:
            user (str): mysql帳號
            password (str): mysql密碼
            database (str): 資料庫
            host (str, optional): 連線主機. Defaults to '127.0.0.1'.
            port (int, optional): 連線port. Defaults to 3306.
        """        # MySQL 連線設定
        self.config = {
            'host': host,
            'port': port,
            'user': user,
            'password': password,
            'database': database
        }
        logger.debug(f'mysql連線設定:\n{self.config}')
        self.sleep_sec = 10

    def set_telegram_info(self, api_key: str, chat_id: str):
        """設定tg相關參數

        Args:
            api_key (str): tg api key
            chat_id (str): 群組 chat id
        """
        self.telegram_api_key = api_key
        self.telegram_chat_id = chat_id

    def set_host(self, host: str):
        """設置mysql連線主機

        Args:
            host (str): 連線主機
        """
        self.config['host'] = host

    def set_port(self, port: int):
        """設置mysql連線port

        Args:
            port (int): 連線port
        """
        self.config['port'] = port

    def set_sleep_sec(self, second: int):
        """設定間隔秒數 預設10秒

        Args:
            second (int): 秒數
        """
        self.sleep_sec = second

    def get_slave_status(self) -> Union[dict, None]:
        """取得 mysql slave狀態

        Returns:
            Union[dict, None]: 若無slave回傳None
        """
        conn = pymysql.connect(**self.config)
        cursor = conn.cursor()
        cursor.execute("SHOW SLAVE STATUS")
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        if result is not None:
            fields = [field[0] for field in cursor.description]
            status = dict(zip(fields, result))
            logger.info(f'mysql slave狀態: {status}')
            return status
        else:
            logger.error('無可用的slave狀態資訊')
            return None

    def send_tg_message(self, msg: str):
        """telegram傳送訊息

        Args:
            msg (str): 傳送訊息內容
        """
        url = f'https://api.telegram.org/bot{self.telegram_api_key}/sendMessage'
        data = {
            'chat_id': self.telegram_chat_id,
            'text': msg
        }
        response = requests.post(url, data=data)
        logger.info(f'telegram傳送訊息結果: {response.json()}')

    def run(self):
        while True:
            status = self.get_slave_status()
            hostname = socket.gethostname()
            if status != None:
                msg = f'主機: {hostname}\nMaster_Log_File:{status["Master_Log_File"]}\Read_Master_Log_Pos: {status["Read_Master_Log_Pos"]}\nSlave_IO_Running: {status["Slave_IO_Running"]}\nSlave_SQL_Running: {status["Slave_SQL_Running"]}'
                self.send_tg_message(msg)
            else:
                self.send_tg_message(f'{hostname} mysql 無可用的slave狀態資訊')
            sleep(self.sleep_sec)
