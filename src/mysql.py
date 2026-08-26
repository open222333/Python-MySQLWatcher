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
            connect_timeout: 連線逾時秒數 預設 5
            read_timeout: 讀取逾時秒數 預設 5
            write_timeout: 寫入逾時秒數 預設 5

        Returns:
            _type_: _description_
        """
        self.logger = kwargs.get('logger')
        if self.logger is None:
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
            'cursorclass': kwargs.get('cursorclass', DictCursor),
            # 連線/讀寫逾時：避免 DB 無回應（例如網路瞬斷、DB 過載）時
            # 監控執行緒被無限期卡住而偵測不到異常
            'connect_timeout': kwargs.get('connect_timeout', 5),
            'read_timeout': kwargs.get('read_timeout', 5),
            'write_timeout': kwargs.get('write_timeout', 5),
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
            # 往上拋出真正的例外，讓呼叫端可以記錄/回報實際失敗原因，
            # 而不是回傳 None 造成呼叫端出現誤導性的 'NoneType' 例外
            raise

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
        if self.logger is None:
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

    # 依序嘗試的 replica 狀態查詢指令：
    # MySQL >= 8.0.22 建議使用 SHOW REPLICA STATUS
    # MySQL 8.4 起已移除 SHOW SLAVE STATUS，因此優先嘗試新指令，失敗時才 fallback
    REPLICA_STATUS_COMMANDS = ('SHOW REPLICA STATUS', 'SHOW SLAVE STATUS')

    # 連續異常達到此次數才發送告警（debounce），避免單次網路/DB瞬斷造成告警誤報。
    # 設為 1 等同於原本「偵測到一次就告警」的行為。
    ANOMALY_THRESHOLD = 2

    def __init__(self, user: str, password: str, database: str, ip: str = '127.0.0.1', port: int = 3306, **kwargs) -> None:
        super().__init__(user, password, database, ip, port, **kwargs)
        self.logger = kwargs.get('logger')
        if self.logger is None:
            self.logger = logging.getLogger('MySQLStatusWatcher')
        # 快取「目前已知可用」的查詢指令，避免每次都要重新嘗試/多一次版本查詢；
        # 若快取的指令執行失敗（例如版本升級/降級），會自動重新偵測，不會被永久卡住。
        self._replica_command = None
        self._consecutive_abnormal = 0

    def _query_status(self, command: str) -> Union[dict, None]:
        """實際執行一次狀態查詢指令，並確保連線一定會被關閉"""
        conn = None
        try:
            conn = MysqlConnect(**self.config, logger=self.logger, name=f'{self.hostname} replica status').get_mysql_connect()
            cursor = conn.cursor()
            cursor.execute(command)
            return cursor.fetchone()
        finally:
            if conn is not None:
                conn.close()

    def get_slave_status(self) -> tuple:
        """取得 replica/slave 狀態，自動依序嘗試相容的指令

        Returns:
            tuple: (status, error_detail)
                status (dict|None): 查詢結果，查詢失敗或無 replica 設定時為 None
                error_detail (str|None): 查詢失敗時的錯誤說明，方便寫入告警訊息追查原因
        """
        commands = []
        if self._replica_command:
            commands.append(self._replica_command)
        commands += [c for c in self.REPLICA_STATUS_COMMANDS if c not in commands]

        last_err = None
        for command in commands:
            try:
                result = self._query_status(command)
                self._replica_command = command
                return result, None
            except pymysql.err.OperationalError as err:
                last_err = err
                # 1064: SQL 語法錯誤 / 1047: unknown command
                # 代表這個 MySQL 版本不支援此指令（例如 8.4 已移除 SHOW SLAVE STATUS），改嘗試下一個
                if err.args and err.args[0] in (1064, 1047) and command != commands[-1]:
                    self.logger.debug(f'{self.hostname} 指令「{command}」不支援 ({err})，改嘗試其他指令')
                    continue
                self.logger.error(f'{self.hostname} 主機連線異常 錯誤代碼 {err.args[0]}: {err.args[1] if len(err.args) > 1 else err}')
                return None, f'OperationalError {err.args[0]}: {err.args[1] if len(err.args) > 1 else err}'
            except Exception as err:
                last_err = err
                self.logger.error(err, exc_info=True)
                return None, str(err)
        self.logger.error(f'{self.hostname} 無法取得 replica 狀態，所有指令皆失敗: {last_err}')
        return None, (str(last_err) if last_err else '未知的 slave 狀態查詢錯誤')

    def _notify(self, msg: str):
        self.logger.info(msg)
        if TELEGRAM_API_KEY and TELEGRAM_CHAT_ID:
            send_tg_message(msg, TELEGRAM_API_KEY, TELEGRAM_CHAT_ID)

    def _build_status_message(self, status: dict) -> tuple:
        """組出告警訊息內容，並帶出延遲秒數/最後錯誤等診斷資訊（若該版本有回傳）

        Returns:
            tuple: (msg, io_running, sql_running)
        """
        io_running = status.get('Replica_IO_Running', status.get('Slave_IO_Running'))
        sql_running = status.get('Replica_SQL_Running', status.get('Slave_SQL_Running'))
        seconds_behind = status.get('Seconds_Behind_Source', status.get('Seconds_Behind_Master'))
        last_io_error = status.get('Last_IO_Error') or None
        last_sql_error = status.get('Last_SQL_Error') or None

        lines = [f'IO_Running: {io_running}', f'SQL_Running: {sql_running}']
        if seconds_behind is not None:
            lines.append(f'延遲秒數(Seconds_Behind): {seconds_behind}')
        if last_io_error:
            lines.append(f'Last_IO_Error: {last_io_error}')
        if last_sql_error:
            lines.append(f'Last_SQL_Error: {last_sql_error}')

        msg = f'\n{self.hostname}  replica同步狀態:\n' + '\n'.join(lines)
        return msg, io_running, sql_running

    def run(self):
        while True:
            try:
                status, err_detail = self.get_slave_status()
                self.logger.debug(f'\nflag: {self.flag}\nstatus: {status}\nerr: {err_detail}')

                if status is not None:
                    msg, io_running, sql_running = self._build_status_message(status)

                    if io_running == 'Yes' and sql_running == 'Yes':
                        self._consecutive_abnormal = 0
                        if self.flag != 'normal':
                            self.flag = 'normal'
                            self._notify(msg)
                    else:
                        if io_running == 'No' and sql_running == 'Yes':
                            new_flag = 'error-IO-running'
                        elif io_running == 'Yes' and sql_running == 'No':
                            new_flag = 'error-SQL-running'
                        else:
                            new_flag = 'error-no-running'

                        self._consecutive_abnormal += 1
                        if self._consecutive_abnormal >= self.ANOMALY_THRESHOLD:
                            if self.flag != new_flag:
                                self.flag = new_flag
                                self._notify(msg)
                        else:
                            self.logger.warning(
                                f'{self.hostname} 偵測到疑似同步異常'
                                f'（第 {self._consecutive_abnormal}/{self.ANOMALY_THRESHOLD} 次，尚未達告警門檻，先觀察不發送告警）\n{msg}'
                            )
                else:
                    self._consecutive_abnormal += 1
                    if self._consecutive_abnormal >= self.ANOMALY_THRESHOLD:
                        if self.flag != 'error':
                            self.flag = 'error'
                            msg = f'{self.hostname}: MySQL replica同步異常\n原因: {err_detail or "未知"}'
                            self._notify(msg)
                    else:
                        self.logger.warning(
                            f'{self.hostname} 查詢 replica 狀態失敗'
                            f'（第 {self._consecutive_abnormal}/{self.ANOMALY_THRESHOLD} 次，尚未達告警門檻）: {err_detail}'
                        )

                self.logger.debug(f'{self.hostname} 監控間隔時間: {get_time_int_str(self.sleep_sec)}')
            except Exception as err:
                # 任何未預期例外都不應該讓這台主機的監控執行緒永久終止；
                # 記錄錯誤後於下一輪繼續監控，而不是 break 離開迴圈導致該主機從此不再被監控
                self.logger.error(f'{self.hostname} 監控迴圈發生未預期例外: {err}', exc_info=True)
            sleep(self.sleep_sec)


class MySQLClusterWatch(MySQLSetting):

    flag = 'initial'

    def __init__(self, user: str, password: str, database: str, ip: str = '127.0.0.1', port: int = 3306, **kwargs) -> None:
        super().__init__(user, password, database, ip, port, **kwargs)
        self.logger = kwargs.get('logger')
        if self.logger is None:
            self.logger = logging.getLogger('MySQLClusterWatch')

    def get_cluster_status(self) -> list:
        """查詢 Group Replication 狀態

        Returns:
            list: 查詢結果，失敗時回傳空 list
        """
        conn = None
        try:
            conn = MysqlConnect(**self.config, logger=self.logger, name=f'{self.hostname} cluster status').get_mysql_connect()
            cursor = conn.cursor()
            cursor.execute("SHOW STATUS LIKE 'group_replication%'")
            return cursor.fetchall()
        except Exception as err:
            self.logger.error(err, exc_info=True)
            return []
        finally:
            if conn is not None:
                conn.close()

    def run(self):
        while True:
            try:
                cluster_status = self.get_cluster_status()
                for status in cluster_status:
                    self.logger.debug(f'{self.hostname}\n{pformat(status)}監控間隔時間: {get_time_int_str(self.sleep_sec)}')
            except Exception as err:
                self.logger.error(err, exc_info=True)
            sleep(self.sleep_sec)
