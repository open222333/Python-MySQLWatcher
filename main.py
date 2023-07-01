from src.logger import Log
from src import LOG_LEVEL
from src.mysql import MySQLStatusWatcher
from argparse import ArgumentParser
import os

parser = ArgumentParser()
parser.add_argument('-u', '--username', type=str, help='mysql帳號', required=True)
parser.add_argument('-p', '--password', type=str, help='mysql密碼', required=True)
parser.add_argument('-d', '--database', type=str, help='mysql 資料庫', required=True)
parser.add_argument('-h', '--host', type=str, help='mysql主機')
parser.add_argument('-P', '--port', type=int, help='mysql port')
parser.add_argument('-s', '--sleep_sec', type=int, help='設定間隔時間')
parser.add_argument('-l', '--log_level', type=str, help='設定紀錄log等級 DEBUG,INFO,WARNING,ERROR,CRITICAL 預設WARNING',
                    choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'])
args = parser.parse_args()


LOG_LEVEL = os.environ.get('LOG_LEVEL', LOG_LEVEL)
TELEGRAM_API_KEY = os.environ.get('TELEGRAM_API_KEY')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

logger = Log()
logger.set_level(LOG_LEVEL)
logger.set_msg_handler()


if __name__ == '__main__':
    if args.log_level:
        logger.set_level(args.log_level)

    watcher = MySQLStatusWatcher(
        user=args.username,
        password=args.password,
        database=args.database
    )
    if args.host:
        watcher.set_host(args.host)
    if args.port:
        watcher.set_port(args.port)
    if args.sleep_sec:
        watcher.set_sleep_sec(args.sleep_sec)
    watcher.run()
