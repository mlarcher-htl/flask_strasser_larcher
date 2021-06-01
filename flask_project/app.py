#!/usr/bin/python

from flask import Flask
import RPi.GPIO as GPIO
import json
import Adafruit_DHT

GPIO.setmode(GPIO.BCM)  # Sets up the RPi lib to use the Broadcom pin mappings
                        #  for the pin names. This corresponds to the pin names
                        #  given in most documentation of the Pi header
GPIO.setwarnings(False) # Turn off warnings that may crop up if you have the
                        #  GPIO pins exported for use via command line
GPIO.setup(5, GPIO.OUT) # Set GPIO2 as an output

sensor=Adafruit_DHT.DHT11
sensor_pin=21

app = Flask(__name__)   # Create an instance of flask called "app"


@app.route("/")         # This is our default handler, if no path is given
def index():
    return "hello"

@app.route('/gpio/<string:id>/<string:level>')
def setGPIOLevel(id, level):
    if level=="toggle":
        GPIO.output(int(id), not(GPIO.input(int(id))))
    elif level == "false":
        GPIO.output(int(id), 0)
    elif level == "true":
        GPIO.output(int(id), 1)
        
    if GPIO.input(int(id)):
        outputState=1
    else:
        outputState=0
    return json.dumps({'state': outputState, 'pin':int(id) }, sort_keys=True, indent=4)

lightPinArray=[5]

@app.route('/light/<string:id>/<string:level>')
def setLightLevel(id, level):
    if level=="toggle":
        GPIO.output(int(lightPinArray[int(id)]), not(GPIO.input(int(lightPinArray[int(id)]))))
    elif level == "false":
        GPIO.output(int(lightPinArray[int(id)]), 0)
    elif level == "true":
        GPIO.output(int(lightPinArray[int(id)]), 1)
        
    if GPIO.input(int(lightPinArray[int(id)])):
        outputState=1
    else:
        outputState=0
    return json.dumps({'state': outputState, 'pin':int(lightPinArray[int(id)]) }, sort_keys=True, indent=4)

@app.route("/climate/")
def getClimateData():
    humidity,temperature=Adafruit_DHT.read_retry(sensor,sensor_pin)
    if (humidity is int and temperature is float):
        return json.dumps({'humidity': "error", 'temperature':"error" }, sort_keys=True, indent=4)
    else:
        return json.dumps({'humidity': int(humidity), 'temperature':float(temperature) }, sort_keys=True, indent=4)

# If we're running this script directly, this portion executes. The Flask
#  instance runs with the given parameters. Note that the "host=0.0.0.0" part
#  is essential to telling the system that we want the app visible to the 
#  outside world.
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
