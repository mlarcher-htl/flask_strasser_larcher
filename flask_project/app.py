import threading
import atexit
from flask import Flask, render_template
from gpiozero import LED, PWMLED
import RPi.GPIO as GPIO
import Adafruit_DHT
import json

POOL_TIME = 60*5 #Alle 5 Minuten werden Wetterdaten erfasst

# variables that are accessible from anywhere
commonDataStruct = {"temperature":998,"humidity":998}
# lock to control access to variable
dataLock = threading.Lock()
# thread handler
climateThread = threading.Thread()

GPIO.setmode(GPIO.BCM)  
GPIO.setwarnings(False) 
led0=PWMLED(5)
led1=PWMLED(6)

climateSensor=Adafruit_DHT.DHT11
climateSensor_pin=21

def create_app():
    app = Flask(__name__)

    def interrupt():
        global climateThread
        climateThread.cancel()

    def readSensor():
        with dataLock:
            humidity,temperature=Adafruit_DHT.read_retry(climateSensor,climateSensor_pin)
            commonDataStruct["temperature"]=temperature
            commonDataStruct["humidity"]=humidity
        print("T: %.2f / H: %.0f" %(temperature,humidity))
    def getPeriodicalClimateData():
        global commonDataStruct
        global climateThread
        readSensor()
        # Set the next thread to happen
        climateThread = threading.Timer(POOL_TIME, getPeriodicalClimateData, ())
        climateThread.start()   

    def initiatePeriodicalClimateData():
        # Do initialisation stuff here
        global climateThread
        # Create your thread
        print("StartThread")
        climateThread = threading.Timer(POOL_TIME, getPeriodicalClimateData, ())
        climateThread.start()

    # Initiate
    initiatePeriodicalClimateData()
    readSensor()
    # When you kill Flask (SIGTERM), clear the trigger for the next thread
    atexit.register(interrupt)
    return app

app = create_app()

@app.after_request #Caching deaktivieren
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


@app.route("/") # Startseite
def index():
    # Read GPIO Status
    led0sts = led0.is_lit
    led1sts = led1.is_lit
    with dataLock:
        temp = commonDataStruct["temperature"]
        humi = commonDataStruct["humidity"]
    #humidity,temperature=Adafruit_DHT.read_retry(Adafruit_DHT.DHT11,21)
    templateData = {
            'led0'  : led0sts,
            'led1'  : led1sts,
            'temperature'  : temp,
            'humidity'  : humi
        }
    return render_template('dashboard2.html', **templateData)

@app.route('/gpio/<string:id>/<string:level>') #Spezielle GPIOs schalten (true, false, toggle)
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

def is_lit(led):
    return led.is_lit
def value(led):
    return led.value

@app.route('/light/<id>/', defaults={'level':None, 'dimlevel': None})
@app.route('/light/<id>/<level>/', defaults={'dimlevel': None}) #die oben indizierten LEDs steuern (true, false, toggle)
@app.route('/light/<id>/<level>/<dimlevel>')
def setLightLevel(id, level, dimlevel):
    if level=="toggle":
        exec("led"+id+".toggle()")
    elif level == "false":
        exec("led"+id+".off()")
    elif level == "true":
       exec("led"+id+".on()")
    elif level == "dim":
        exec("led"+id+".value="+str(float(dimlevel)/100))
        
    if exec("led"+id+".is_lit"):
        outputState=0
    else:
        outputState=1
    #exec("dimlevel=led"+id+".value")
    return json.dumps({'state': is_lit(eval("led"+id)), 'dimlevel': value(eval("led"+id))*100, 'pin':int(lightPinArray[int(id)]) }, sort_keys=True, indent=4)

@app.route("/climate/") #Klimadaten abrufen
def getClimateData():
    with dataLock:
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