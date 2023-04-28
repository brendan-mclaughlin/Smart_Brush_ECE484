import os
import time
import ipaddress
import wifi
import socketpool
import busio
import board
import microcontroller
import displayio
import adafruit_adxl34x
from digitalio import DigitalInOut, Direction
from adafruit_httpserver.server import HTTPServer
from adafruit_httpserver.request import HTTPRequest
from adafruit_httpserver.response import HTTPResponse
from adafruit_httpserver.methods import HTTPMethod
from adafruit_httpserver.mime_type import MIMEType

#  onboard LED setup
led = DigitalInOut(board.LED)
led.direction = Direction.OUTPUT
led.value = False

# Setup I2C accelerometer
i2c = busio.I2C(sda = board.GP4, scl = board.GP5)
accelerometer = adafruit_adxl34x.ADXL343(i2c)
accelerometer.enable_motion_detection()
status_text = "Not Brushing"

#  connect to network
print()
print("Connecting to WiFi")

#  set static IP address
ipv4 =  ipaddress.IPv4Address("192.168.1.42")
netmask =  ipaddress.IPv4Address("255.255.255.0")
gateway =  ipaddress.IPv4Address("192.168.1.1")
wifi.radio.set_ipv4_address(ipv4=ipv4,netmask=netmask,gateway=gateway)
#  connect to your SSID
wifi.radio.connect(os.getenv('CIRCUITPY_WIFI_SSID'), os.getenv('CIRCUITPY_WIFI_PASSWORD'))

print("Connected to WiFi")
pool = socketpool.SocketPool(wifi.radio)
server = HTTPServer(pool)

#  font for HTML
font_family = "monospace"

#  the HTML script
#  setup as an f string
#  this way, can insert string variables from code.py directly
#  of note, use {{ and }} if something from html *actually* needs to be in brackets
#  i.e. CSS style formatting
def webpage():
	[] = read_data()
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta http-equiv="refresh" content="1" />
    <meta http-equiv="Content-type" content="text/html;charset=utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
    html{{font-family: {font_family}; background-color: lightgrey;
    display:inline-block; margin: 0px auto; text-align: center;}}
      h1{{color: deeppink; width: 200; word-wrap: break-word; padding: 2vh; font-size: 35px;}}
      p{{font-size: 1.5rem; width: 200; word-wrap: break-word;}}
      .button{{font-family: {font_family};display: inline-block;
      background-color: black; border: none;
      border-radius: 4px; color: white; padding: 16px 40px;
      text-decoration: none; font-size: 30px; margin: 2px; cursor: pointer;}}
      p.dotted {{margin: auto;
      width: 75%; font-size: 25px; text-align: center;}}
    </style>
    </head>
    <body>
    <title>Pico W HTTP Server</title>
    <h1>Pico W HTTP Server</h1>
    <br>
    <p class="dotted">This is a Pico W running an HTTP server with CircuitPython.</p>
    <h1>Control the LED on the Pico W with these buttons:</h1><br>
    <br>
    <h1>Brushing Teeth?</h>
    <p class="dotted">{status_text}</p>
    </br>
    <form accept-charset="utf-8" method="POST">
    <button class="button" name="LED ON" value="ON" type="submit">LED ON</button></a></p></form>
    <p><form accept-charset="utf-8" method="POST">
    <button class="button" name="LED OFF" value="OFF" type="submit">LED OFF</button></a></p></form>
    <p><form accept-charset="utf-8" method="POST">
    <button class="button" name="party" value="party" type="submit">PARTY!</button></a></p></form>
    </body></html>
    """
    return html

#  route default static IP
@server.route("/")
def base(request: HTTPRequest):  # pylint: disable=unused-argument
    #  serve the HTML f string
    #  with content type text/html
    with HTTPResponse(request, content_type=MIMEType.TYPE_HTML) as response:
        response.send(f"{webpage()}")

#  if a button is pressed on the site
@server.route("/", method=HTTPMethod.POST)
def buttonpress(request: HTTPRequest):
    #  get the raw text
    raw_text = request.raw_request.decode("utf8")
    print(raw_text)
    #  if the led on button was pressed
    if "ON" in raw_text:
        #  turn on the onboard LED
        led.value = True
    #  if the led off button was pressed
    if "OFF" in raw_text:
        #  turn the onboard LED off
        led.value = False
    #  reload site
    with HTTPResponse(request, content_type=MIMEType.TYPE_HTML) as response:
        response.send(f"{webpage()}")

print("starting server..")
# startup the server
try:
    server.start(str(wifi.radio.ipv4_address))
    print("Listening on http://%s:80" % wifi.radio.ipv4_address)
#  if the server fails to begin, restart the pico w
except OSError:
    time.sleep(5)
    print("restarting..")
    microcontroller.reset()

ping_address = ipaddress.ip_address("8.8.4.4")

clock = time.monotonic() #  time.monotonic() holder for server ping

brushing_clock = time.monotonic()
brushing_session = false
start_time = 0
end_time = 0
fail_counter = 0

while True:
    try:
        #  every 30 seconds, ping server & update temp reading
        if (clock + 30) < time.monotonic():
            if wifi.radio.ping(ping_address) is None:
                print("lost connection")
            else:
                print("connected")
            clock = time.monotonic()
        #  poll the server for incoming/outgoing requests
        # every 1 second check acceleromter
        if (brushing_clock + .5) < time.monotonic() and brushing_session:
        	if(!accelerometer.events["motion"])
        		fail_counter = fail_counter + 1
        	else:
        		fail_counter = 0
        		
        if fail_counter > 5:
        	end_time = time.monotonic()
        	brushing_session = false
        
        if (brushing_clock + 120) < time.monotonic():
        	end_time = 120
        	brushing_session = false        	
                	
        if(accelerometer.events["motion"]):
            status_text = "Brushing"
        else:
            status_text = "Not Brushing"
        server.poll()
    # pylint: disable=broad-except
    except Exception as e:
        print(e)
        continue
