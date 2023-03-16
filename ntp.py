import socket, struct, time
from machine import RTC

from logs import log


def get_ntp_time() -> int:
    """Make 3 attempts to get the current time from pool.ntp.org and set the system clock if successful,
    otherwise raise an exception

    Args: none

    Returns: UNIX epoch seconds
    """
    NTP_DELTA = 2208988800  # first day of the year 1970
    HOST = "pool.ntp.org"
    NTP_QUERY = bytearray(48)
    NTP_QUERY[0] = 0x1B
    addr = socket.getaddrinfo(HOST, 123)[0][-1]
    for attempt in range(3):
        log("Requesting time from pool.ntp.org, attempt {attempt}")
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        _ = s.sendto(NTP_QUERY, addr)
        msg = s.recv(48)
        s.close()
        val = struct.unpack("!I", msg[40:44])[0]
        return val - NTP_DELTA  # breaks out of the loop
    raise RuntimeError("Failed to get time from pool.ntp.org")


def set_system_clock(ntp_time: int, tz_offset_hours: int) -> None:
    """Attempts to set the system clock from pool.ntp.org

    Args: tz_offset (int): timezone offset in hours from UTC

    Returns: None
    """
    # this is speculative. Send a one-off request to pool.ntp.org, and it fails we move on
    secs = ntp_time + tz_offset_hours * 3600
    dt_tuple = time.gmtime(secs)
    log(f"Got epoch seconds {secs}, datetime {dt_tuple}")
    RTC().datetime([dt_tuple[i] for i in (0, 1, 2, 6, 3, 4, 5)] + [0])
