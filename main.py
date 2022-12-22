import time
import network
from machine import Pin, I2C
import ujson as json
import uasyncio as asyncio
from ahttpserver import HTTPResponse, HTTPServer
from ahttpserver.sse import EventSource

def setup_i2c():
    # Returns a function that returns the sensor output as a float
    # 
    # This implementation connects to a VEML6030 sensor on pins 20 and 21 of a Pi Pico.
    # Adjust the connection details to match your setup.

    # I2C connection definitions
    I2C_BUS=0
    I2C_SDA=Pin(20)
    I2C_SCL=Pin(21)
    I2C_FREQ=100000
    # VEML6030 Register definitions
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
    # Return a function that reads the sensor
    async def read_sensor() -> float:
        data = i2c.readfrom_mem(_veml6030Address, _REG_ALS, 2)
        return int.from_bytes(data, "little") * 0.0576  # [lx/bit]
    return read_sensor

def setup_wifi():
    # Get wifi credentials from file "wifi.json".
    # DO NOT COMMIT wifi.json TO VERSION CONTROL!
    # the file format is:
    # {
    #     "ssid": "your-ssid",
    #     "password": "your-password"
    # }
    f = open("wifi.json", "r")
    wifi_config = json.load(f)
    f.close()
    ssid = wifi_config["ssid"]
    password = wifi_config["password"]

    wlan = network.WLAN(network.STA_IF)

    # Pico-W firmware doesn't yet allow setting the hostname, (see https://github.com/micropython/micropython/pull/8918)
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
        print(f"waiting for connection ({max_wait})")
        time.sleep(1)
    # Handle connection error
    if wlan.status() != 3:
        raise RuntimeError("Network connection failed")
    else:
        print("MAC = " + wlan.config("mac").hex()) #type: ignore
        print("IP  = " + wlan.ifconfig()[0])


read_sensor = setup_i2c()
app = HTTPServer()

async def lux_json_response():
    lux = await read_sensor()
    response_json = {"id": "sensor-ambient_light", "state": f"{lux} lx", "value": lux}
    return json.dumps(response_json)

@app.route("GET", "/sensor/ambient_light")
async def sensor_ambient_light(reader, writer, request):
    response = HTTPResponse(200, "application/json", close=True)
    await response.send(writer)
    await writer.drain()
    writer.write(await lux_json_response())
    await writer.drain()


@app.route("GET", "/events")
async def events(reader, writer, request):
    eventsource = await EventSource.init(reader, writer)
    while True:
        await asyncio.sleep(2)
        t = time.localtime()
        try:
            await eventsource.send(event="state", data=await lux_json_response())
        except Exception:
            break  # close connection

if __name__ == "__main__":
    setup_wifi()
    loop = asyncio.get_event_loop()
    loop.create_task(app.start())
    loop.run_forever()
