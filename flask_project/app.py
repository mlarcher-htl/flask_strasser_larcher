import threading #Threading wird für Hintergrund-Sensor-Werte-Erfassen benötigt
import atexit
from flask import Flask, render_template
from gpiozero import LED, PWMLED
#import RPi.GPIO as GPIO
import Adafruit_DHT
import json

led0=PWMLED(5) #GPIOZERO Funktion für LEDs mit variabler Helligkeit
led1=PWMLED(6) #GPIOZERO Funktion für LEDs mit variabler Helligkeit
lightPinArray=[5,6] #Hier sind die Pins der LEDs angegeben

climateSensor=Adafruit_DHT.DHT11
climateSensor_pin=21
climateSensorReloadTime = 60 * 7 #Alle 7 Minuten wird ein neuer Sensorwert im Hintergrund bestimmt

commonDataStruct = {"temperature":998,"humidity":998} #Die Klimawerte - Wenn 998 bedeutet das, dass noch nie der Sensor gelesen werden konnte
dataLock = threading.Lock() #Threading Lock um Mehrfachzugriffe zu vermeiden
climateThread = threading.Thread() #ThreadingHandler

""" #Wird nicht benötigt, da wir auf die /gpio/xx Funktionen verzichten
GPIO.setmode(GPIO.BCM)  
GPIO.setwarnings(False)
"""

def create_app():
    app = Flask(__name__) #app erstellen

    def interrupt():
        global climateThread
        climateThread.cancel() #wenn app geschlossen wird, dann Thread abbrechen

    def readSensor(): #Sensorwerte vom DHT11 lesen und in CommonDataStruct speichern
        with dataLock:
            humidity,temperature=Adafruit_DHT.read_retry(climateSensor,climateSensor_pin)
            commonDataStruct["temperature"]=temperature
            commonDataStruct["humidity"]=humidity
        print("T: %.2f / H: %.0f" %(temperature,humidity))
        
    def getPeriodicalClimateData(): 
        global commonDataStruct
        global climateThread

        readSensor() #Sensorwerte lesen und abspeichern

        climateThread = threading.Timer(climateSensorReloadTime, getPeriodicalClimateData, ())
        climateThread.start()   #Neuen Thread starten, welcher nach 7? Minuten ausgeführt wird

    def initiatePeriodicalClimateData(): #Diese Funktion wird nur einmal bei der App-Erstellung ausgeführt und startet den "Loop" von Threads
        global climateThread
        print("StartThread")
        climateThread = threading.Timer(climateSensorReloadTime, getPeriodicalClimateData, ())
        climateThread.start()

    # Initiate
    initiatePeriodicalClimateData() #climateThread starten
    readSensor() #Gleich zu Beginn/Start des Webservers Sensorwerte bestimmen
    atexit.register(interrupt) #Beim Exit interrupt-Funktion aufrufen -> Thread abbrechen
    return app

app = create_app()

@app.after_request #Caching deaktivieren
def add_header(r):
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r


@app.route("/") # Startseite
def index():
    # GPIO Status lesen
    led0sts = led0.is_lit
    led1sts = led1.is_lit
    with dataLock: #Die Klimawerte werden aus dem commonDataStruct genommen und in die HTML eingefügt
        temp = commonDataStruct["temperature"]
        humi = commonDataStruct["humidity"]
    templateData = {
            'led0'  : led0sts,
            'led1'  : led1sts,
            'temperature'  : temp,
            'humidity'  : humi
        }
    return render_template('dashboard.html', **templateData) #Das Template darstellen, mit der templateData(status,klimadaten,...)

"""
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
""" #Die GPIO Funktion wurde entfernt, da man sowieso die vorher bereits definierten LEDs steuern möchte



#Hilfsfunktionen
def is_lit(led):
    return led.is_lit
def value(led):
    return led.value

@app.route('/light/<id>/', defaults={'level':None, 'dimlevel': None})
@app.route('/light/<id>/<level>/', defaults={'dimlevel': None}) #die oben indizierten LEDs steuern (true, false, toggle)
@app.route('/light/<id>/<level>/<dimlevel>')
def setLightLevel(id, level, dimlevel):
    if level=="toggle":
        exec("led"+id+".toggle()") #LED umschalten
    elif level == "false":
        exec("led"+id+".off()") #LED ausschalten
    elif level == "true":
       exec("led"+id+".on()") #LED einschalten
    elif level == "dim":
        exec("led"+id+".value="+str(float(dimlevel)/100)) #LED auf <dimlevel> % dimmen

    #mittels is_lit(led) und value(led) werden die Rückgabekontrollwerte bestimmt
    return json.dumps({'state': is_lit(eval("led"+id)), 'dimlevel': value(eval("led"+id))*100, 'pin':int(lightPinArray[int(id)]) }, sort_keys=True, indent=4)

@app.route("/climate/") #Klimadaten abrufen
def getClimateData():
    with dataLock:
        temperature = commonDataStruct["temperature"]
        humidity = commonDataStruct["humidity"]
    
    if (humidity is int and temperature is float):
        return json.dumps({'humidity': 999, 'temperature': 999 }, sort_keys=True, indent=4) #999 -> NoneType Sensor Reading
    else:
        return json.dumps({'humidity': int(humidity), 'temperature':float(temperature) }, sort_keys=True, indent=4)

#Wenn man explizit dieses File ausführt wird folgendes ausgeführt
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)