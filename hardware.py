import time
from machine import Pin, I2C
from logs import log

# VEML6030 constants - see https://www.vishay.com/docs/84305/designingveml6030.pdf
# We set the sensor to 1x gain, 100ms integration time, 1x persistence, and disable interrupt
# Global variables are used as they are needed in multiple functions
VEML6030_ADDRESS = 0x10
VEML6030_ALS_CONF = 0x00
VEML6030_ALS_REG = 0x04
VEML6030_DEFAULT_SETTINGS = (
    b"\x00"  # gain:1x, integration 100ms, persistence 1, disable interrupt
)
VEML6030_CONVERSION_FACTOR = 0.0576

# I2C constants.  This implementation connects to a sensor on pins 26 and 27 of a Pi Pico.
# Adjust the connection details to match your specific hardware
I2C_BUS = 1
I2C_SDA = Pin(26)
I2C_SCL = Pin(27)
I2C_FREQ = 100000

_i2c_instance: I2C


async def read_sensor() -> float:
    # Reads the sensor and converts the output to lux
    global _i2c_instance
    data = _i2c_instance.readfrom_mem(VEML6030_ADDRESS, VEML6030_ALS_REG, 2)
    return int.from_bytes(data, "little") * VEML6030_CONVERSION_FACTOR


def setup_i2c() -> None:
    global _i2c_instance
    log(
        f"Setting up I2C connection, Bus: {I2C_BUS}, SDA: {I2C_SDA}, SCL: {I2C_SCL}, Freq: {I2C_FREQ}"
    )
    _i2c_instance = I2C(I2C_BUS, sda=I2C_SDA, scl=I2C_SCL, freq=I2C_FREQ)
    time.sleep(1)
    _i2c_instance.writeto_mem(
        VEML6030_ADDRESS, VEML6030_ALS_CONF, VEML6030_DEFAULT_SETTINGS
    )
    # Give the sensor time to process the settings before allowing the caller to use it
    log("I2C config done, pausing for 1s for device to settle")
    time.sleep(1)
