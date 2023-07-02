import requests
import logging


def get_chat_id(api_token: str, watch_logger: logging = None):
    response = requests.get(f"https://api.telegram.org/bot{api_token}/getUpdates")

    if response.status_code == 200:
        data = response.json()
        if watch_logger:
            watch_logger.debug(f'取得telegram chat id: {data}')
        if "result" in data and data["result"]:
            chat_id = data["result"][0]["message"]["chat"]["id"]
            return chat_id
    else:
        watch_logger.error(f'取得telegram chat id發生錯誤: {response.json()}')
    return None


def send_tg_message(msg: str, telegram_api_key: str, telegram_chat_id: str, watch_logger: logging = None):
    """telegram傳送訊息

    Args:
        msg (str): 傳送訊息內容
    """
    try:
        url = f'https://api.telegram.org/bot{telegram_api_key}/sendMessage'
        data = {
            'chat_id': telegram_chat_id,
            'text': msg
        }
        response = requests.post(url, data=data)
        if watch_logger:
            watch_logger.info(f'telegram傳送訊息結果: {response.json()}')
    except Exception as err:
        if watch_logger:
            watch_logger.error(err, exc_info=True)
