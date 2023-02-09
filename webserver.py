import ujson as json
import utime as time
import uasyncio as asyncio
from ahttpserver import HTTPResponse, HTTPServer
from ahttpserver.sse import EventSource

from hardware import read_sensor
from logs import log, logbuffer

last_lux = 300.00
app = HTTPServer()


async def lux_json_response() -> str:
    # Returns a JSON string with the current lux value
    global last_lux
    try:
        last_lux = await read_sensor()
    except Exception as e:
        # Ignore all read errors, just use the last value
        log(f"Error reading sensor, reusing last read value: {last_lux}: {str(e)}")
    response_json = {
        "id": "sensor-ambient_light",
        "state": f"{last_lux} lx",
        "value": last_lux,
    }
    return json.dumps(response_json)


@app.route("GET", "/sensor/ambient_light")
async def sensor_ambient_light(reader, writer, request):
    # Respond to synchronous requests with the current lux value
    response = HTTPResponse(200, "application/json", close=True)
    await response.send(writer)
    await writer.drain()
    writer.write(await lux_json_response())
    await writer.drain()


@app.route("GET", "/events")
async def events(reader, writer, request):
    # Send an update very 2 seconds
    eventsource = await EventSource.init(reader, writer)
    while True:
        await asyncio.sleep(2)
        t = time.localtime()
        try:
            await eventsource.send(event="state", data=await lux_json_response())
        except Exception:
            break  # close connection


@app.route("GET", "/logs")
async def logs(reader, writer, request):
    response = HTTPResponse(200, "text/plain", close=True)
    await response.send(writer)
    await writer.drain()
    writer.write("\n".join(logbuffer()))
    await writer.drain()
