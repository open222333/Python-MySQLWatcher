from . import TELEGRAM_API_KEY, TELEGRAM_CHAT_ID
from .tool import get_time_int_str
from .telegram import send_tg_message
from .logger import Log
from typing import Union
from time import sleep
import pymysql
import socket


class MySQLStatusWatcher():

    def __init__(self, user: str, password: str, database: str, logger: Log, ip: str = '127.0.0.1', port: int = 3306) -> None:
        """mysql 狀態 監控程式

        Args:
            user (str): mysql帳號
            password (str): mysql密碼
            database (str): 資料庫
            logger (logging): 紀錄log
            ip (str, optional): 連線主機. Defaults to '127.0.0.1'.
            port (int, optional): 連線port. Defaults to 3306.
        """        # MySQL 連線設定
        self.config = {
            'host': ip,
            'port': port,
            'user': user,
            'password': password,
            'database': database
        }
        self.sleep_sec = 10
        self.logger = logger
        self.hostname = socket.gethostname()

    def set_telegram_info(self, api_key: str, chat_id: str):
        """設定tg相關參數

        Args:
            api_key (str): tg api key
            chat_id (str): 群組 chat id
        """
        self.telegram_api_key = api_key
        self.telegram_chat_id = chat_id

    def set_hostname(self, hostname: str):
        """設置顯示主機名稱

        Args:
            hostname (str): 主機名稱
        """
        self.hostname = hostname

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
        except pymysql.err.OperationalError as err:
            self.logger.error(f'{self.hostname} 主機連線異常 錯誤代碼 {err.args[0]}: {err.args[1]}')
        except Exception as err:
            self.logger.error(err, exc_info=True)

    def run(self):
        flag = 'initial'
        while True:
            try:
                status = self.get_slave_status()
                if status != None:
                    slave_io_running = status["Slave_IO_Running"]
                    slave_sql_running = status["Slave_SQL_Running"]
                    msg = f'\n{self.hostname}  slave同步狀態:\nSlave_IO_Running: {slave_io_running}\nSlave_SQL_Running: {slave_sql_running}'
                    if slave_io_running == 'Yes' and slave_sql_running == 'Yes':
                        if flag != 'normal':
                            flag = 'normal'
                            self.logger.info(msg)
                            if TELEGRAM_API_KEY and TELEGRAM_CHAT_ID:
                                send_tg_message(msg, TELEGRAM_API_KEY, TELEGRAM_CHAT_ID)
                    if slave_io_running == 'No' and slave_sql_running == 'Yes':
                        if flag != 'error-slave-IO-running':
                            flag = 'error-slave-IO-running'
                            self.logger.info(msg)
                            if TELEGRAM_API_KEY and TELEGRAM_CHAT_ID:
                                send_tg_message(msg, TELEGRAM_API_KEY, TELEGRAM_CHAT_ID)
                    if slave_io_running == 'Yes' and slave_sql_running == 'No':
                        if flag != 'error-slave-SQL-running':
                            flag = 'error-slave-SQL-running'
                            self.logger.info(msg)
                            if TELEGRAM_API_KEY and TELEGRAM_CHAT_ID:
                                send_tg_message(msg, TELEGRAM_API_KEY, TELEGRAM_CHAT_ID)
                    else:
                        if flag != 'error-no-running':
                            flag = 'error-no-running'
                            self.logger.info(msg)
                            if TELEGRAM_API_KEY and TELEGRAM_CHAT_ID:
                                send_tg_message(msg, TELEGRAM_API_KEY, TELEGRAM_CHAT_ID)
                else:
                    if flag != 'error':
                        flag = 'error'
                        msg = f'{self.hostname}: MySQL slave同步異常'
                        self.logger.error(msg)
                        if TELEGRAM_API_KEY and TELEGRAM_CHAT_ID:
                            send_tg_message(msg, TELEGRAM_API_KEY, TELEGRAM_CHAT_ID)
                self.logger.debug(f'{self.hostname} 監控間隔時間: {get_time_int_str(self.sleep_sec)}')
                sleep(self.sleep_sec)
            except Exception as err:
                self.logger.error(err, exc_info=True)
                break
