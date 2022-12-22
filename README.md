# An ambient light sensor for lunar.fyi using a Pi Pico W

Based on code from https://github.com/alin23/lunarsensor, and using Erik Delange's micropython async HTTP server (https://github.com/erikdelange/MicroPython-HTTP-Server).

You'll need to create a file "wifi.json" in the project root before uploading to your Pico W, in the following format

```json
{
    "ssid": "your-ssid",
    "password": "your-password"
}
```
  
Since the "hostname" option to wifi.config isn't working yet on the Pico W (as of 2022-12-22, see https://github.com/micropython/micropython/pull/8918), you'll need to give the device a fixed IP and configure lunersensor.local in the hosts file of the machine running lunar.