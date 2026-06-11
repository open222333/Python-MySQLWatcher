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

        self.name = kwargs.get('name', '未命名 mysql 連線')

        # mysql 連線設定
        self.set_setting(**kwargs)

    def set_setting(self, **kwargs):
        self.setting = {
            'host': kwargs.get('host', '127.0.0.1'),
            'port': int(kwargs.get('port', 3306)),
            'database': kwargs.get('database'),
            'user': kwargs.get('username'),
            'password': kwargs.get('password'),
            'charset': kwargs.get('charset', 'utf8mb4'),
            'autocommit': bool(kwargs.get('autocommit', True)),
            'cursorclass': kwargs.get('cursorclass', DictCursor)
        }

    def get_mysql_connect(self) -> Connection:
        """取得 mysql 連線

        Returns:
            _type_: _description_
        """
        try:
            mysql_connect = pymysql.connect(**self.setting)
            self.logger.debug(f'取得 mysql_connect - {self.name}\n設定:\n{pformat(self.setting, sort_dicts=False)}')
            return mysql_connect
        except Exception as err:
            self.logger.error(f'取得 mysql 連線 - {self.name} 發生錯誤: {err}\n設定:\n{pformat(self.setting, sort_dicts=False)}', exc_info=True)

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

    flag = 'initial'

    def __init__(self, user: str, password: str, database: str, ip: str = '127.0.0.1', port: int = 3306, **kwargs) -> None:
        super().__init__(user, password, database, ip, port, **kwargs)
        self.logger = kwargs.get('logger')
        if self.logger == None:
            self.logger = logging.getLogger('MySQLStatusWatcher')
        self._mysql_version = None

    def _fetch_mysql_version(self) -> tuple:
        """查詢 MySQL 版本號，回傳 (major, minor, patch) tuple"""
        try:
            conn = MysqlConnect(**self.config).get_mysql_connect()
            cursor = conn.cursor()
            cursor.execute("SELECT VERSION()")
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            version_str = list(row.values())[0].split("-")[0]
            return tuple(int(p) for p in version_str.split(".")[:3])
        except Exception as err:
            self.logger.error(f'{self.hostname} 取得 MySQL 版本失敗: {err}', exc_info=True)
            return (0, 0, 0)

    @property
    def mysql_version(self) -> tuple:
        """取得 MySQL 版本（快取，只查一次）"""
        if self._mysql_version is None:
            self._mysql_version = self._fetch_mysql_version()
            ver_str = ".".join(str(v) for v in self._mysql_version)
            self.logger.info(f'{self.hostname} MySQL 版本: {ver_str}')
        return self._mysql_version

    def get_slave_status(self) -> Union[dict, None]:
        """取得 replica/slave 狀態，依版本使用對應指令

        MySQL >= 8.4 使用 SHOW REPLICA STATUS
        舊版使用 SHOW SLAVE STATUS

        Returns:
            Union[dict, None]: 若無 replica/slave 回傳 None
        """
        try:
            conn = MysqlConnect(**self.config).get_mysql_connect()
            cursor = conn.cursor()
            if self.mysql_version >= (8, 4, 0):
                cursor.execute("SHOW REPLICA STATUS")
            else:
                cursor.execute("SHOW SLAVE STATUS")
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            return result if result is not None else None
        except pymysql.err.OperationalError as err:
            self.logger.error(f'{self.hostname} 主機連線異常 錯誤代碼 {err.args[0]}: {err.args[1]}')
        except Exception as err:
            self.logger.error(err, exc_info=True)

    def run(self):
        while True:
            try:
                status = self.get_slave_status()
                self.logger.debug(f'\nflag: {self.flag}\nstatus: {status}')
                if status != None:
                    if self.mysql_version >= (8, 4, 0):
                        io_running = status.get("Replica_IO_Running")
                        sql_running = status.get("Replica_SQL_Running")
                    else:
                        io_running = status.get("Slave_IO_Running")
                        sql_running = status.get("Slave_SQL_Running")
                    msg = f'\n{self.hostname}  replica同步狀態:\nIO_Running: {io_running}\nSQL_Running: {sql_running}'
                    if io_running == 'Yes' and sql_running == 'Yes':
                        if self.flag != 'normal':
                            self.flag = 'normal'
                            self.logger.info(msg)
                            if TELEGRAM_API_KEY and TELEGRAM_CHAT_ID:
                                send_tg_message(msg, TELEGRAM_API_KEY, TELEGRAM_CHAT_ID)
                    elif io_running == 'No' and sql_running == 'Yes':
                        if self.flag != 'error-IO-running':
                            self.flag = 'error-IO-running'
                            self.logger.info(msg)
                            if TELEGRAM_API_KEY and TELEGRAM_CHAT_ID:
                                send_tg_message(msg, TELEGRAM_API_KEY, TELEGRAM_CHAT_ID)
                    elif io_running == 'Yes' and sql_running == 'No':
                        if self.flag != 'error-SQL-running':
                            self.flag = 'error-SQL-running'
                            self.logger.info(msg)
                            if TELEGRAM_API_KEY and TELEGRAM_CHAT_ID:
                                send_tg_message(msg, TELEGRAM_API_KEY, TELEGRAM_CHAT_ID)
                    else:
                        if self.flag != 'error-no-running':
                            self.flag = 'error-no-running'
                            self.logger.info(msg)
                            if TELEGRAM_API_KEY and TELEGRAM_CHAT_ID:
                                send_tg_message(msg, TELEGRAM_API_KEY, TELEGRAM_CHAT_ID)
                else:
                    if self.flag != 'error':
                        self.flag = 'error'
                        msg = f'{self.hostname}: MySQL replica同步異常'
                        self.logger.error(msg)
                        if TELEGRAM_API_KEY and TELEGRAM_CHAT_ID:
                            send_tg_message(msg, TELEGRAM_API_KEY, TELEGRAM_CHAT_ID)
                self.logger.debug(f'{self.hostname} 監控間隔時間: {get_time_int_str(self.sleep_sec)}')
                sleep(self.sleep_sec)
            except Exception as err:
                self.logger.error(err, exc_info=True)
                break


class MySQLClusterWatch(MySQLSetting):

    flag = 'initial'

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

        while True:
            try:
                cluster_status = self.get_cluster_status()
                for status in cluster_status:
                    self.logger.debug(f'{self.hostname}\n{pformat(status)}監控間隔時間: {get_time_int_str(self.sleep_sec)}')
                sleep(self.sleep_sec)
            except Exception as err:
                self.logger.error(err, exc_info=True)
                break
