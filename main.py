from src import LOG_LEVEL, LOG_FILE_DISABLE, HOSTS
from src.logger import Log
from src.mysql import MySQLStatusWatcher
from argparse import ArgumentParser
import threading

watch_logger = Log()
watch_logger.set_level(LOG_LEVEL)
if not LOG_FILE_DISABLE:
    watch_logger.set_file_handler()
watch_logger.set_msg_handler()


parser = ArgumentParser()
parser.add_argument('-s', '--sleep_sec', type=int, help='設定間隔時間', required=False)
parser.add_argument(
    '-l', '--log_level', type=str,
    help='設定紀錄log等級 DEBUG,INFO,WARNING,ERROR,CRITICAL 預設WARNING',
    choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], required=False
)
args = parser.parse_args()

if __name__ == '__main__':
    if args.log_level:
        watch_logger.set_level(args.log_level)

    for host in HOSTS:
        watch_logger.info(f'\n主機資訊: {host["hostname"]} - {host["ip"]}:{host["port"]}\nmysql使用者: {host["username"]}')
        watcher = MySQLStatusWatcher(
            ip=host['ip'],
            port=host['port'],
            user=host['username'],
            password=host['password'],
            database=host['database'],
            logger=watch_logger
        )

        watcher.set_hostname(host['hostname'])
        if args.sleep_sec:
            watcher.set_sleep_sec(args.sleep_sec)

        threading.Thread(target=watcher.run).start()
