import utime as time
import uasyncio as asyncio
import ujson as json
import machine

from logs import log

import webserver
import wifi
import hardware

# Timezone offset in hours from UTC (used for logging)
TZ_OFFSET = 8

# Default lux value to use if the sensor_reader fails on the first call.  On subsequent calls the last value will be used.
DEFAULT_LUX = 300

if __name__ == "__main__":
    # See README.md for wifi credential file format and handling
    with open("wifi.json", "r") as f:
        wifi_config = json.load(f)
        WIFI_SSID = wifi_config["ssid"]
        WIFI_PASSWORD = wifi_config["password"]

    try:
        hardware.setup_i2c()
        wifi.setup_wifi(WIFI_SSID, WIFI_PASSWORD)
        wifi.maybe_set_system_clock(TZ_OFFSET)
        server = webserver.make_webserver(hardware.read_sensor, DEFAULT_LUX)
        loop = asyncio.get_event_loop()
        task = loop.create_task(
            server.start()
        )  # always keep a reference to the task so it doesn't get garbage collected
        loop.run_forever()  # this blocks until an exception is encountered
    except Exception as e:
        # all sorts of things could have happened, best to log what we know, wait a bit, and reset the device
        log(f"RESETTING: {str(e)}")
        time.sleep(10)
        machine.reset()
