#
# formatter test for 4 digits 7 segments display
#
import time
from string import printable
import numpy as np
import paho.mqtt.client as mqtt

TOPIC_HOME_FLY_RESULT = "stat/tasmota_144AF2/RESULT"
TOPIC_HOME_FLY_CMND = "cmnd/tasmota_144AF2/"
TOPIC_HOME_FLY_CMND_DIMMER = TOPIC_HOME_FLY_CMND + "DisplayDimmer"
TOPIC_HOME_FLY_CMND_DISPLAY_TEXT = TOPIC_HOME_FLY_CMND + "DisplayText"
TOPIC_HOME_FLY_CMND_DISPLAY_FLOAT = TOPIC_HOME_FLY_CMND + "DisplayFloat"
TOPIC_HOME_FLY_CMND_DISPLAY_CLOCK = TOPIC_HOME_FLY_CMND + "DisplayClock"

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("$SYS/#")


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(msg.topic + " " + str(msg.payload))


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("192.168.147.1", 1883, 60)

client.publish(topic=TOPIC_HOME_FLY_CMND_DISPLAY_TEXT, payload="____")
time.sleep(1)

# for c in printable:
#     if c >= 'Z':
#         print(c)
#         client.publish(topic=TOPIC_HOME_FLY_CMND_DISPLAY_TEXT, payload=c)
#         time.sleep(2)

for d in np.arange(-10.5, 10.5, 0.1):
    d = round(d, 1)
    if d == -0.0:
        d = abs(d)
    print(d)
    client.publish(topic=TOPIC_HOME_FLY_CMND_DISPLAY_TEXT, payload=f"{d:.1f}".replace('.', '`'))
    time.sleep(1)

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
client.loop_forever()
