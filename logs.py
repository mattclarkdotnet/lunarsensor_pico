import utime as time

"""
Simple logging function to keep a buffer of the last 100 log messages so we can make them available at the /logs endpoint
"""
_logbuffer: list = []
_logbuffer_max = 100


def logbuffer() -> list:
    return _logbuffer


def log(log_message: str) -> None:
    """Log a message to the console and the log buffer with the local time added, and restricts the log buffer to the last 100 messages.

    Args: log_message (str): the message to log

    Returns: None
    """
    global _logbuffer
    if len(_logbuffer) > _logbuffer_max:
        _logbuffer.pop(0)
    now = time.gmtime()
    # convert datetime tuple to iso 8601 string
    date_str = (
        f"{now[0]}-{now[1]:02d}-{now[2]:02d}T{now[3]:02d}:{now[4]:02d}:{now[5]:02d}Z"
    )
    log_line = f"{date_str}: {log_message}"
    print(log_line)
    _logbuffer.append(log_line)
