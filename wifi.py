import socket, struct, network, time
from machine import RTC
from logs import log


def setup_wifi(ssid, password) -> None:
    """Attempt to connect to the given SSID/PWD for 20 seconds, and raise an exception on failure

    Args:
        ssid (str): SSID of the network to connect to
        password (str): Password for the network to connect to

    Returns: None

    Raises:
        RuntimeError: If the connection fails
    """
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    # Wait for a good connection status for 20 seconds, and return if successful, otherwise raise an exception
    for attempt in range(1, 20):
        log(
            f"Waiting for connection: wlan.status == {wlan.status()}, attempt {attempt})"
        )
        time.sleep(1)
        if wlan.status() == 3:
            log("MAC = " + wlan.config("mac").hex())  # type: ignore
            log("IP  = " + wlan.ifconfig()[0])
            return
    # Handle connection error
    raise RuntimeError(f"Network connection failed, wlan.status == {wlan.status()}")


def get_ntp_time() -> int:
    """Get the current time from pool.ntp.org, and set the system clock if successful

    Args: none

    Returns: UNIX epoch seconds
    """
    log("Requesting time from pool.ntp.org")
    NTP_DELTA = 2208988800  # first day of the year 1970
    host = "pool.ntp.org"
    NTP_QUERY = bytearray(48)
    NTP_QUERY[0] = 0x1B
    addr = socket.getaddrinfo(host, 123)[0][-1]
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    res = s.sendto(NTP_QUERY, addr)
    msg = s.recv(48)
    s.close()
    val = struct.unpack("!I", msg[40:44])[0]
    return val - NTP_DELTA


def maybe_set_system_clock(tz_offset) -> None:
    """Attempts to set the system clock from pool.ntp.org, and logs the result.  Ignores any exceptions.

    Args: tz_offset (int): timezone offset in hours from UTC

    Returns: None
    """
    try:
        # this is speculative. Send a one-off request to pool.ntp.org, and it fails we move on
        secs = get_ntp_time() + tz_offset * 3600
        dt_tuple = time.gmtime(secs)
        log(f"Got epoch seconds {secs}, datetime {dt_tuple}")
        RTC().datetime([dt_tuple[i] for i in (0, 1, 2, 6, 3, 4, 5)] + [0])
    except Exception as e:
        log(f"Failed to set RTC: {str(e)}")
