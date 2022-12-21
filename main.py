import time
import network
import ujson
from machine import Pin, I2C

# I2C connection definitions
I2C_BUS=0
I2C_SDA=Pin(20)
I2C_SCL=Pin(21)
I2C_FREQ=100000

# I2C Register definitions
_veml6030Address = 0x10
_ALS_CONF = 0x00
_REG_ALS = 0x04
_DEFAULT_SETTINGS = (
    b"\x00"  # initialise gain:1x, integration 100ms, persistence 1, disable interrupt
)

# Create an I2C connection to the VEML6030
i2c=I2C(I2C_BUS, sda=I2C_SDA, scl=I2C_SCL, freq=I2C_FREQ)
# Write the default settings to the VEML6030
i2c.writeto_mem(_veml6030Address, _ALS_CONF, _DEFAULT_SETTINGS)
# Give the sensor time to process the settings
time.sleep(1)

# Get wifi credentials from file
f = open("wifi.json", "r")
wifi_config = ujson.load(f)
f.close()
ssid = wifi_config["ssid"]
password = wifi_config["password"]


def setup_wifi():
    wlan = network.WLAN(network.STA_IF)
    # Waiting for https://github.com/micropython/micropython/pull/8918 to be fixed for Pico-W
    # so the device can announce lunarsensor.local over mDNS/DHCP
    # In the meantime, set lunarsensor.local in the DHCP server for this MAC, or in the hosts file
    # of the computer running Lunar
    #
    # wlan.config(hostname='lunarsensor.local')
    #
    wlan.active(True)
    wlan.connect(ssid, password)
    # Wait for connect or fail
    max_wait = 10
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        max_wait -= 1
        print("waiting for connection...")
        time.sleep(1)
    # Handle connection error
    if wlan.status() != 3:
        raise RuntimeError("Network connection failed")
    else:
        print("MAC = " + wlan.config("mac").hex())
        print("IP  = " + wlan.ifconfig()[0])

def read_sensor():
    data = i2c.readfrom_mem(_veml6030Address, _REG_ALS, 2)
    return int.from_bytes(data, "little") * 0.0576  # [lx/bit]

setup_wifi()

import uasyncio as asyncio

from ahttpserver import HTTPResponse, HTTPServer, sendfile

app = HTTPServer()


@app.route("GET", "/")
async def root(reader, writer, request):
    response = HTTPResponse(200, "text/html", close=True)
    await response.send(writer)
    await sendfile(writer, "index.html")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(app.start())
    loop.run_forever()


while True:
    print(read_sensor())
    time.sleep(5)
