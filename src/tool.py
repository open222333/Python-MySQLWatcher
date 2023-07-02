from typing import Union


def get_time_int_str(total_seconds: Union[int, float]) -> str:
    """依照秒數 回傳中文時間

    Args:
        total_seconds (int): 總秒數

    Returns:
        str: 回傳時間
    """
    msg = ''
    seconds = total_seconds % 60
    minutes = (total_seconds // 60) % 60
    hours = ((total_seconds // 60) // 60) % 24
    days = ((total_seconds // 60) // 60) // 24
    if days != 0:
        msg += f"{int(days)}天"
    if hours != 0:
        msg += f"{int(hours)}時"
    if minutes != 0:
        msg += f"{int(minutes)}分"
    if seconds != 0:
        msg += f"{int(round(seconds, 0))}秒"
    return msg
