#!/usr/bin/python
from flask import Flask, render_template, request
import RPi.GPIO as GPIO
import json
import Adafruit_DHT
import time
import threading
import atexit




GPIO.setmode(GPIO.BCM)  # Sets up the RPi lib to use the Broadcom pin mappings
                        #  for the pin names. This corresponds to the pin names
                        #  given in most documentation of the Pi header
GPIO.setwarnings(False) # Turn off warnings that may crop up if you have the
                        #  GPIO pins exported for use via command line
GPIO.setup(5, GPIO.OUT) # Set GPIO2 as an output
GPIO.setup(6, GPIO.OUT) # Set GPIO2 as an output

app = Flask(__name__)   # Create an instance of flask called "app"

@app.after_request
def add_header(r):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r


@app.route("/")         # This is our default handler, if no path is given
def index():
    # Read GPIO Status
    led0sts = GPIO.input(5)
    led1sts = GPIO.input(6)
    #humidity,temperature=Adafruit_DHT.read_retry(Adafruit_DHT.DHT11,21)
    templateData = {
            'led0'  : led0sts,
            'led1'  : led1sts,
            'temperature'  : 22.2,
            'humidity'  : 33
        }
    return render_template('dashboard2.html', **templateData)

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

lightPinArray=[5,6]

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
    temperature = commonDataStruct["temperature"]
    humidity = commonDataStruct["humidity"]
    
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
    
