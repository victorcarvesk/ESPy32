"""
MicroPython IoT Weather Station Example for Wokwi.com

To view the data:

1. Go to http://www.hivemq.com/demos/websocket-client/
2. Click "Connect"
3. Under Subscriptions, click "Add New Topic Subscription"
4. In the Topic field, type "wokwi-weather" then click "Subscribe"

Now click on the DHT22 sensor in the simulation,
change the temperature/humidity, and you should see
the message appear on the MQTT Broker, in the "Messages" pane.

Copyright (C) 2022, Uri Shaked

https://wokwi.com/arduino/projects/322577683855704658
"""

import network
from utime import sleep
from umachine import Pin, Timer
from umqtt.simple import MQTTClient
import ujson

with open('mqtt_info.json','r') as mqtt_file:
    mqtt_info = ujson.load(mqtt_file)

# MQTT Server Parameters
MQTT_CLIENT_ID = mqtt_info['MQTT_CLIENT_ID']
MQTT_BROKER = mqtt_info['MQTT_BROKER']
MQTT_USER = mqtt_info['MQTT_USER']
MQTT_PASSWORD = mqtt_info['MQTT_PASSWORD']
MQTT_TOPIC = mqtt_info['MQTT_TOPIC']

def do_connect(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('connecting to network...')
        wlan.connect(ssid, password)
        while not wlan.isconnected():
            pass
    print('network config:', wlan.ifconfig())
    
do_connect(mqtt_info['WIFI_SSID'], mqtt_info['WIFI_PASSWORD'])

sleep(5)

print("Connecting to MQTT server... ", end="")
client = MQTTClient(
    MQTT_CLIENT_ID, MQTT_BROKER, user=MQTT_USER, password=MQTT_PASSWORD)
client.connect()

print("Connected!")

# while True:
#     client.publish(MQTT_TOPIC, "Hi, I'm here!")
#     time.sleep(2)

led = Pin(2, Pin.OUT)

def blink_led(topic, msg):
    print(f"A mensagem recebida é: {msg}")
    msg = msg.decode()
    print(f"A mensagem decodificada é: {msg}")
    if msg == 'on':
        led.on()
    elif msg =='off':
        led.off()
        
client.set_callback(blink_led)
client.subscribe(MQTT_TOPIC)

def tick(timer):
    client.check_msg()

tim1 = Timer(0)
tim1.init(period=1000, mode=Timer.PERIODIC, callback=tick)
