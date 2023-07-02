import socket
import pymysql
from time import sleep
from typing import Union
from . import TELEGRAM_API_KEY, TELEGRAM_CHAT_ID
from .tool import get_time_int_str
from .telegram import send_tg_message
from .logger import Log


class MySQLStatusWatcher():

    def __init__(self, user: str, password: str, database: str, logger: Log, host: str = '127.0.0.1', port: int = 3306) -> None:
        """mysql 狀態 監控程式

        Args:
            user (str): mysql帳號
            password (str): mysql密碼
            database (str): 資料庫
            logger (logging): 紀錄log
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
        self.sleep_sec = 10
        self.logger = logger

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
        try:
            conn = pymysql.connect(**self.config)
            cursor = conn.cursor()
            cursor.execute("SHOW SLAVE STATUS")
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            if result is not None:
                fields = [field[0] for field in cursor.description]
                status = dict(zip(fields, result))
                return status
            else:
                return None
        except Exception as err:
            self.logger.error(err, exc_info=True)

    def run(self):
        is_sended = False
        while True:
            try:
                status = self.get_slave_status()
                hostname = socket.gethostname()
                if status != None:
                    if not is_sended:
                        msg = f'主機 {hostname}:\nMaster_Log_File:{status["Master_Log_File"]}\Read_Master_Log_Pos: {status["Read_Master_Log_Pos"]}\nSlave_IO_Running: {status["Slave_IO_Running"]}\nSlave_SQL_Running: {status["Slave_SQL_Running"]}'
                        self.logger.info(msg)
                        if TELEGRAM_API_KEY and TELEGRAM_CHAT_ID:
                            send_tg_message(msg, TELEGRAM_API_KEY, TELEGRAM_CHAT_ID)
                            is_sended = False
                else:
                    if not is_sended:
                        msg = f'主機 {hostname}: MySQL slave狀態異常'
                        self.logger.error(msg)
                        if TELEGRAM_API_KEY and TELEGRAM_CHAT_ID:
                            send_tg_message(msg, TELEGRAM_API_KEY, TELEGRAM_CHAT_ID)
                            is_sended = True
                self.logger.debug(f'監控間隔時間: {get_time_int_str(self.sleep_sec)}')
                sleep(self.sleep_sec)
            except Exception as err:
                self.logger.error(err, exc_info=True)
                break
