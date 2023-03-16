import network, time

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


