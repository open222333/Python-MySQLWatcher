from . import TELEGRAM_API_KEY, TELEGRAM_CHAT_ID
from .tool import get_time_int_str
from .telegram import send_tg_message
from .logger import Log
from typing import Union
from time import sleep
from pprint import pformat
from pymysql.cursors import DictCursor
from pymysql.connections import Connection
import logging
import pymysql
import socket


class MysqlConnect():

    def __init__(self, **kwargs) -> None:
        """建立 mysql 連線

        Args:
            logger (logging, optional): logger
            host: 預設 127.0.0
            port: 預設 3306
            database: 資料庫
            username: 用戶
            password: 密碼
            charset: 預設 utf8mb4
            autocommit: 預設 True
            cursorclass: 預設 DictCursor

        Returns:
            _type_: _description_
        """
        self.logger = kwargs.get('logger')
        if self.logger == None:
            self.logger = logging.getLogger('MongoConnect')

        self.name: kwargs.get('name', '未命名 mysql 連線')

        # mysql 連線設定
        self.setting = {
            'host': kwargs.get('host', '127.0.0.1'),
            'port': int(kwargs.get('port', 3306)),
            'database': kwargs.get('database'),
            'username': kwargs.get('username'),
            'password': kwargs.get('password'),
            'charset': kwargs.get('charset', 'utf8mb4'),
            'autocommit': bool(kwargs.get('autocommit', True)),
            'cursorclass': kwargs.get('cursorclass', DictCursor)
        }

    def __call__(self, **kwds):
        return self.get_mysql_connect(kwds)

    def get_mysql_connect(self, **kwargs) -> Connection:
        """取得 mysql 連線

        Returns:
            _type_: _description_
        """
        try:
            mysql_connect = pymysql.connect(**kwargs)
            self.logger.debug(f'取得 mysql_connect - {self.name}\n設定:\n{pformat(kwargs, sort_dicts=False)}')
            return mysql_connect
        except Exception as err:
            self.logger.error(f'取得 mysql 連線 - {self.name} 發生錯誤: {err}\n設定:\n{pformat(kwargs, sort_dicts=False)}', exc_info=True)

    def get_mysql_setting(self):
        return self.setting


class MySQLSetting():

    def __init__(self, user: str, password: str, database: str, ip: str = '127.0.0.1', port: int = 3306, **kwargs) -> None:
        """mysql 設定

        Args:
            user (str): mysql帳號
            password (str): mysql密碼
            database (str): 資料庫
            ip (str, optional): 連線主機. Defaults to '127.0.0.1'.
            port (int, optional): 連線port. Defaults to 3306.
        """

        # MySQL 連線設定
        self.config = {
            'host': ip,
            'port': port,
            'user': user,
            'password': password,
            'database': database
        }

        self.logger = kwargs.get('logger')
        if self.logger == None:
            self.logger = logging.getLogger('MySQLSetting')

        self.sleep_sec = 10
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

    def set_sleep_sec(self, second: int):
        """設定間隔秒數 預設10秒

        Args:
            second (int): 秒數
        """
        self.sleep_sec = second


class MySQLStatusWatcher(MySQLSetting):

    def __init__(self, user: str, password: str, database: str, ip: str = '127.0.0.1', port: int = 3306, **kwargs) -> None:
        super().__init__(user, password, database, ip, port, **kwargs)
        self.logger = kwargs.get('logger')
        if self.logger == None:
            self.logger = logging.getLogger('MySQLStatusWatcher')

    def get_slave_status(self) -> Union[dict, None]:
        """取得 mysql slave狀態

        Returns:
            Union[dict, None]: 若無slave回傳None
        """
        try:
            # conn = pymysql.connect(**self.config)
            conn = MysqlConnect(**self.config)
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


class MySQLClusterWatch(MySQLSetting):

    def __init__(self, user: str, password: str, database: str, ip: str = '127.0.0.1', port: int = 3306, **kwargs) -> None:
        super().__init__(user, password, database, ip, port, **kwargs)
        self.logger = kwargs.get('logger')
        if self.logger == None:
            self.logger = logging.getLogger('MySQLClusterWatch')

    def get_cluster_status(self):
        # 連接 MySQL Cluster
        try:
            connection = MysqlConnect(**self.config)
            if connection.is_connected():
                self.logger.info('Connected to MySQL Cluster')
                cursor = connection.cursor(dictionary=True)
                cursor.execute("SHOW STATUS LIKE 'group_replication%'")
                cluster_status = cursor.fetchall()
                return cluster_status
        except Exception as err:
            self.logger.error(err, exc_info=True)
        finally:
            # 確保關閉連接
            if 'connection' in locals() and connection.is_connected():
                cursor.close()
                connection.close()
                self.logger.info(f'{connection.name} MySQL connection closed')

    def run(self):
        flag = 'initial'
        while True:
            try:
                cluster_status = self.get_cluster_status()
                for status in cluster_status:
                    self.logger.debug(f'{self.hostname}\n{pformat(status)}監控間隔時間: {get_time_int_str(self.sleep_sec)}')
                sleep(self.sleep_sec)
            except Exception as err:
                self.logger.error(err, exc_info=True)
                break
