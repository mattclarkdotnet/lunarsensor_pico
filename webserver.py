import ujson as json
import utime as time
import uasyncio as asyncio
from ahttpserver import HTTPResponse, HTTPServer
from ahttpserver.sse import EventSource

from logs import log, logbuffer


def make_webserver(sensor_reader, default_lux) -> HTTPServer:
    """Make a webserver that responds to requests for sensor data and logs

    The endpoints registered are:
        /sensor/ambient_light: responds to synchronous requests with the current lux value
        /events: sends an update every 2 seconds
        /logs: responds with the last 100 log messages
    The endpoint methods get registered with the server, and the server is returned to and started by the caller, so no references are lost.

    Args:
        sensor_reader (function): a function that returns the current sensor reading
        default_lux (int): the default lux value to use if the sensor_reader fails on the first call.  On subsequent calls the last value will be used.

    Returns:
        HTTPServer: a webserver that responds to requests for sensor data and logs
    """
    server = HTTPServer()
    last_lux = default_lux  # We need a default so the first request to lux_json_response doesn't return an error

    async def lux_json_response() -> str:
        # Returns a JSON string with the current lux value
        nonlocal last_lux
        try:
            last_lux = await sensor_reader()
        except Exception as e:
            # Ignore all read errors, just use the last value
            log(f"Error reading sensor, reusing last read value: {last_lux}: {str(e)}")
        response_json = {
            "id": "sensor-ambient_light",
            "state": f"{last_lux} lx",
            "value": last_lux,
        }
        return json.dumps(response_json)

    @server.route("GET", "/sensor/ambient_light")
    async def sensor_ambient_light(reader, writer, request):
        # Respond to synchronous requests with the current lux value
        response = HTTPResponse(200, "application/json", close=True)
        await response.send(writer)
        await writer.drain()
        writer.write(await lux_json_response())
        await writer.drain()

    @server.route("GET", "/events")
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

    @server.route("GET", "/logs")
    async def logs(reader, writer, request):
        response = HTTPResponse(200, "text/plain", close=True)
        await response.send(writer)
        await writer.drain()
        writer.write("\n".join(logbuffer()))
        await writer.drain()

    return server
