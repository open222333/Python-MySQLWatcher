from src import LOG_LEVEL, LOG_FILE_DISABLE, HOSTS, MONITORING_INTERVAL
from src.logger import Log
from src.mysql import MySQLStatusWatcher, MySQLClusterWatch
from argparse import ArgumentParser
import threading

logger = Log('MAIN')
logger.set_level(LOG_LEVEL)
if not LOG_FILE_DISABLE:
    logger.set_file_handler()
logger.set_msg_handler()


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument('-s', '--sleep_sec', type=int, help='設定間隔時間', required=False)
    parser.add_argument('-t', '--type', choices=['master_slave', 'cluster'], help='監控', default='master_slave')
    parser.add_argument(
        '-l', '--log_level', type=str,
        help='設定紀錄log等級 DEBUG,INFO,WARNING,ERROR,CRITICAL 預設WARNING',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], required=False
    )
    args = parser.parse_args()

    if __name__ == '__main__':
        if args.log_level:
            logger.set_level(args.log_level)

        if args.type == 'master_slave':
            for host in HOSTS:
                logger.info(f'\n主機資訊: {host["hostname"]} - {host["ip"]}:{host["port"]}\nmysql使用者: {host["username"]}')
                if args.type == 'master_slave':
                    watcher = MySQLStatusWatcher(
                        ip=host['ip'],
                        port=host['port'],
                        user=host['username'],
                        password=host['password'],
                        database=host['database'],
                        logger=logger
                    )
                elif args.type == 'cluster':
                    watcher = MySQLClusterWatch(
                        ip=host['ip'],
                        port=host['port'],
                        user=host['username'],
                        password=host['password'],
                        database=host['database'],
                        logger=logger
                    )

                watcher.set_hostname(host['hostname'])
                if args.sleep_sec:
                    watcher.set_sleep_sec(args.sleep_sec)
                if MONITORING_INTERVAL != 10:
                    watcher.set_sleep_sec(MONITORING_INTERVAL)

                threading.Thread(target=watcher.run).start()
