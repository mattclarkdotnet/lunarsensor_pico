# An ambient light sensor for lunar.fyi using a Pi Pico W and MicroPython

This is a remote ambient light sensor for https://lunar.fyi.  It is based on code from https://github.com/alin23/lunarsensor.

It expands on the simpler example server by adding robust error handling and reporting during both setup and runtime.  It also provides logs and syncs time during startup using NTP. 

The hardware used is a Pi Pico W and a VEML6030 ambient light sensor.

## Network configuration

You'll need to create a file "wifi.json" in the project root before uploading to your Pico W, in the following format

```json
{
    "ssid": "your-ssid",
    "password": "your-password"
}
```

Since the "hostname" option to wifi.config isn't working yet on the Pico W (as of 2022-12-22, see https://github.com/micropython/micropython/pull/8918), you'll need to give the device a fixed IP and configure lunarsensor.local in the hosts file of the machine running lunar.

## Hardware configuration

The default hardware configuration is set in the hardware.py file.  Modify the I2C_ constants as needed for your setup

``` python
I2C_BUS = 1
I2C_SDA = Pin(26)
I2C_SCL = Pin(27)
I2C_FREQ = 100000
```
## HTTP serving

We use a vendored copy of Erik Delange's micropython async HTTP server (https://github.com/erikdelange/MicroPython-HTTP-Server).

The only change is to avoid raising exceptions in the response path, instead printing an error to the console.  The most likely reason for an error is an I2C bus issue in hardware.py/read_sensor, so instead of complicating the top level logic in main.py, the code has been adjusted to send an HTTP 500 response.