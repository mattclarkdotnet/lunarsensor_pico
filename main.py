import utime as time
import uasyncio as asyncio
import ujson as json
from machine import reset as machine_reset

from logs import log
from webserver import app
from wifi import setup_wifi, set_system_clock
from hardware import setup_i2c

# Timezone offset in hours from UTC (used for logging)
TZ_OFFSET = 8

if __name__ == "__main__":
    # Get wifi credentials from file "wifi.json".
    # DO NOT COMMIT wifi.json TO VERSION CONTROL!
    # the file format is:
    # {
    #     "ssid": "your-ssid",
    #     "password": "your-password"
    # }
    with open("wifi.json", "r") as f:
        wifi_config = json.load(f)
        wifi_ssid = wifi_config["ssid"]
        wifi_password = wifi_config["password"]

    try:
        setup_wifi(wifi_ssid, wifi_password)
        try:
            set_system_clock(TZ_OFFSET)
        except Exception as e:
            log(f"Failed to set system clock, {str(e)}")
            # Don't raise the exception, this non-fatal error only means the log times will be wrong
        setup_i2c()
        loop = asyncio.get_event_loop()
        loop.create_task(app.start())
        loop.run_forever()  # this blocks until an exception is encountered
    except Exception as e:
        # all sorts of things could have happened, best to log what we know, wait a bit, and reset the device
        log(f"RESETTING: {str(e)}")
        time.sleep(10)
        machine_reset()
