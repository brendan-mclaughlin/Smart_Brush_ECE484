import os
import time
import ipaddress
import wifi
import socketpool
import ssl
import busio
import board
import microcontroller
import adafruit_adxl34x
import adafruit_requests
from digitalio import DigitalInOut, Direction
from adafruit_httpserver.server import HTTPServer
from adafruit_httpserver.request import HTTPRequest
from adafruit_httpserver.response import HTTPResponse
from adafruit_httpserver.methods import HTTPMethod
from adafruit_httpserver.mime_type import MIMEType

#  Status LED setup
led = DigitalInOut(board.LED)
led.direction = Direction.OUTPUT
led.value = False

green = DigitalInOut(board.GP19)
green.direction = Direction.OUTPUT
green.value = True
time.sleep(.1)
green.value = False

yellow = DigitalInOut(board.GP18)
yellow.direction = Direction.OUTPUT
yellow.value = True
time.sleep(.1)
yellow.value = False

red = DigitalInOut(board.GP17)
red.direction = Direction.OUTPUT
red.value = True
time.sleep(.1)
red.value = False


blue = DigitalInOut(board.GP16)
blue.direction = Direction.OUTPUT
blue.value = True
time.sleep(.1)
blue.value = False

stats = open("stats.csv", "a+")

# Setup I2C accelerometer
i2c = busio.I2C(sda = board.GP4, scl = board.GP5)
accelerometer = adafruit_adxl34x.ADXL343(i2c)
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
wifi.radio.connect(os.getenv('WIFI_SSID'), os.getenv('WIFI_PASSWORD'))

print("Connected to WiFi")
pool = socketpool.SocketPool(wifi.radio)

url = "http://worldtimeapi.org/api/timezone/America/Chicago"
requests = adafruit_requests.Session(pool, ssl.create_default_context())
try:
    response = requests.get(url)
    response_as_json = response.json()
    day_of_week = response_as_json['day_of_week']
          
except Exception as error:
    day_of_week = "8"


server = HTTPServer(pool)

def update_stats():
    global stats
    stats.seek(0)
    totals = [0 for i in range(8)]
    averages = [0 for i in range(8)]
    total = 0
    average = 0
    
    for line in stats.readlines():
        data = line.split(",")
        if data[0] == "1": #Monday
            totals[1] += 1
            averages[1] += int(data[1])
            total += 1
            average += int(data[1])
            
        elif data[0] == "2": #Tuesday
            totals[2] += 1
            averages[2] += int(data[1])
            total += 1
            average += int(data[1])
            
        elif data[0] == "3": #Wednesday
            totals[3] += 1
            averages[3] += int(data[1])
            total += 1
            average += int(data[1])
            
        elif data[0] == "4": #Thursday
            totals[4] += 1
            averages[4] += int(data[1])
            total += 1
            average += int(data[1])
            
        elif data[0] == "5": #Friday
            totals[5] += 1
            averages[5] += int(data[1])
            total += 1
            average += int(data[1])
            
        elif data[0] == "6": #Saturday
            totals[6] += 1
            averages[6] += int(data[1])
            total += 1
            average += int(data[1])
            
        elif data[0] == "0": #Sunday
            totals[0] += 1
            averages[0] += int(data[1])
            total += 1
            average += int(data[1])
            
        else:
            totals[7] += 1
            averages[7] += int(data[1])
            total += 1
            average += int(data[1])
            
    for i in range(0, 7):
        averages[i] = averages[i] / totals[i]
            
    average = average / total
        
    return totals, averages, total, average
            

#  the HTML script
#  setup as an f string
#  this way, can insert string variables from code.py directly
#  of note, use {{ and }} if something from html *actually* needs to be in brackets
#  i.e. CSS style formatting
def webpage():
    [totals, averages, total, average] = update_stats()
    html = f"""
    <!DOCTYPE html>
    <html>
      <head>
        <title>Weekly Data</title>
      </head>
      <body style="background-color:powderblue;">
        <table>
          <tr style="background-color:white;">
            <td>Monday</td>
            <td>Tuesday</td>
            <td>Wednesday</td>
            <td>Thursday</td>
            <td>Friday</td>
            <td>Saturday</td>
            <td>Sunday</td>
          </tr>
          <tr style="background-color:lightgrey;">
            <td>Total: {totals[1]}</td>
            <td>Total: {totals[2]}</td>
            <td>Total: {totals[3]}</td>
            <td>Total: {totals[4]}</td>
            <td>Total: {totals[5]}</td>
            <td>Total: {totals[6]}</td>
            <td>Total: {totals[0]}</td>
          </tr>
          <tr style="background-color:lightgrey;">
            <td>Average: {averages[1]}</td>
            <td>Average: {averages[2]}</td>
            <td>Average: {averages[3]}</td>
            <td>Average: {averages[4]}</td>
            <td>Average: {averages[5]}</td>
            <td>Average: {averages[6]}</td>
            <td>Average: {averages[0]}</td>
          </tr>
        </table>
        <table>
          <tr style="background-color:white;">
            <td>Average (Weekly)</td>
            <td>Total (Weekly)</td>
            <td>Offline Brushes</td>
          </tr>
          <tr style="background-color:lightgrey;">
            <td>{total}</td>
            <td>{average}</td>
            <td>Total: {totals[8]}</td>
          </tr>
          <tr style="background-color:lightgrey;">
            <td></td>
            <td></td>
            <td>Average: {averages[8]}</td>
          </tr>
        </table>
      </body>
    </html>
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

if wifi.radio.ping(ping_address) is None:
    blue.value = False
    print("lost connection")
else:
    blue.value = True
    print("connected")

red.value = True
accelerometer.enable_tap_detection(tap_count=2)

while not accelerometer.events["tap"]:
    pass

accelerometer.disable_tap_detection()
accelerometer.enable_motion_detection()

red.value = False
green.value = True
print("Start Brushing!")

clock = time.time() 

start_time = time.time()
brushing_clock = time.time()
brushing_session = True
start_time = time.time()
end_time = 0
fail_counter = 0

while True:
    try:
        #  every 30 seconds, ping server
        if time.time() - clock > 30:
            if wifi.radio.ping(ping_address) is None:
                blue.value = False
                print("lost connection")
            else:
                blue.value = True
                print("connected")
            clock = time.time()
        #  poll the server for incoming/outgoing requests
        # every .5 seconds check acceleromter
        if (time.time() - brushing_clock > 0.5) and brushing_session:
            if not accelerometer.events["motion"]:
                green.value = False
                yellow.value = True
                fail_counter = fail_counter + 1
                print("Brush HARDER!")
            else:
                yellow.value = False
                green.value = True
                fail_counter = 0
            brushing_clock = time.time()
            
        if fail_counter > 6 and brushing_session:
            green.value = False
            yellow.value = False
            red.value = True
            end_time = time.time() - start_time
            brushing_session = False
            print("Didn't Brush Hard Enough")
            stats.write("{},{}\n".format(day_of_week, end_time))
            stats.flush()
        
        if (time.time() - start_time) > 120 and brushing_session:
            green.value = False
            yellow.value = False
            red.value = True
            end_time = 120
            brushing_session = False
            print("Done Brushing!")
            stats.write("{},{}\n".format(day_of_week, end_time))
            stats.flush()
            
        server.poll()
    # pylint: disable=broad-except
    except Exception as e:
        print(e)
        continue
