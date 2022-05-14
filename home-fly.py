#
# home-fly controller 26.4.2022
# hardware: ESP8266, 3 buttons, 1 LED 4 digits
# firmware: tasmota 11.1.0
# for productions rus inside ha-appdaemon add-on
#
# button left   = meteo: single mostra meteo + meteo unhold, double meteo hold
# button center = power meter: single mostra power, double mostra clock
# button right  = boiler: single simple toggle on/off
#

TOPIC_HOME_FLY_RESULT = "stat/tasmota_144AF2/RESULT"
TOPIC_HOME_FLY_CMND = "cmnd/tasmota_144AF2/"
TOPIC_HOME_FLY_CMND_DIMMER = TOPIC_HOME_FLY_CMND + "DisplayDimmer"
TOPIC_HOME_FLY_CMND_DISPLAY_TEXT = TOPIC_HOME_FLY_CMND + "DisplayText"
TOPIC_HOME_FLY_CMND_DISPLAY_CLOCK = TOPIC_HOME_FLY_CMND + "DisplayClock"

POWER_METER_EVENT = "sensor.total_watt"
METEO_EVENT = "weather.casatorino2022"
METEO_STATE = METEO_EVENT
BOILER_STATE = "switch.boiler"
ENTITY_SWITCH_BOILER = 'switch.boiler'

# --------------------------------------------------------------------
# end of configuration
# --------------------------------------------------------------------

import appdaemon.plugins.hass.hassapi as hass
import appdaemon.plugins.mqtt.mqttapi as mqtt
import json
import datetime as dt

DISPLAY_STATE_CLOCK = 0
DISPLAY_STATE_POWER_METER = 1
DISPLAY_STATE_METEO = 2
DISPLAY_STATE_BOILER = 3

METEO_TEXT = {
    "clear-night": "SERE",
    "cloudy": "NUVO",
    "exceptional": "EXCP",
    "fog": "NEbb",
    "hail": "GRAN",
    "lightning": "TEMP",
    "lightning-rainy": "TMPP",
    "partlycloudy": "PNUV",
    "pouring": "ROVE",
    "rainy": "PIOG",
    "snowy": "NEVE",
    "snowy-rainy": "NEVP",
    "sunny": "SOLE",
    "windy": "VENT",
    "windy-variant": "PVEN"
}


class HomeFly(hass.Hass):

    def initialize(self):
        # mqtt buttons
        self.mqtt = self.get_plugin_api("MQTT")
        self.mqtt.mqtt_subscribe(topic=TOPIC_HOME_FLY_RESULT)
        self.mqtt.listen_event(self.mqttEvent, "MQTT_MESSAGE", topic=TOPIC_HOME_FLY_RESULT, namespace='mqtt')
        # LED display service
        self.insideDimmerRange = False
        self.displayState = DISPLAY_STATE_CLOCK
        self.run_minutely(self.displayUpdate, dt.time(0, 0, 0))
        # power meter events
        self.totalW = '----'
        self.listen_event(self.powerMeterEvent, 'state_changed', entity_id=POWER_METER_EVENT)
        # meteo events
        self.meteoHoldOption = False
        self.meteoText = METEO_TEXT[self.get_state(METEO_STATE)]
        self.listen_event(self.meteoEvent, 'state_changed', entity_id=METEO_EVENT)

    def mqttEvent(self, event_name, data, *args, **kwargs):
        pld = json.loads(data['payload'])
        if 'Button1' in pld.keys():
            Button1 = pld['Button1']['Action']
            if (Button1 == 'SINGLE'):
                self.meteoHoldOption = False
            elif (Button1 == 'DOUBLE'):
                self.meteoHoldOption = True
            self.mqtt.mqtt_publish(TOPIC_HOME_FLY_CMND_DISPLAY_TEXT, self.meteoText)
        if 'Button2' in pld.keys():
            Button2 = pld['Button2']['Action']
            if (Button2 == 'SINGLE'):
                self.displayState = DISPLAY_STATE_POWER_METER
                self.mqtt.mqtt_publish(TOPIC_HOME_FLY_CMND_DISPLAY_TEXT, self.totalW)
            elif (Button2 == 'DOUBLE'):
                self.displayState = DISPLAY_STATE_CLOCK
                self.mqtt.mqtt_publish(TOPIC_HOME_FLY_CMND_DISPLAY_CLOCK, 2)
        if 'Button3' in pld.keys():
            Button3 = pld['Button3']['Action']
            if (Button3 == 'SINGLE'):
                if (self.get_state(BOILER_STATE) == 'on'):
                    self.call_service("switch/turn_off", entity_id=ENTITY_SWITCH_BOILER)
                    self.mqtt.mqtt_publish(TOPIC_HOME_FLY_CMND_DISPLAY_TEXT, "OFF")
                elif (self.get_state(BOILER_STATE) == 'off'):
                    self.call_service("switch/turn_on", entity_id=ENTITY_SWITCH_BOILER)
                    self.mqtt.mqtt_publish(TOPIC_HOME_FLY_CMND_DISPLAY_TEXT, "ON")
                else:
                    self.call_service("switch/turn_off", entity_id=ENTITY_SWITCH_BOILER)
                    self.mqtt.mqtt_publish(TOPIC_HOME_FLY_CMND_DISPLAY_TEXT, "OFF")

    def displayUpdate(self, *args, **kwargs):
        weekday = dt.datetime.now().weekday() + 1  # lun == 1
        # display dimmer time range
        if (self.now_is_between("22:00:00", "08:00:00")):
            if (not self.insideDimmerRange):
                self.insideDimmerRange = True
                self.mqtt.mqtt_publish(TOPIC_HOME_FLY_CMND_DIMMER, 20)
        else:
            if (self.insideDimmerRange):
                self.insideDimmerRange = False
                self.mqtt.mqtt_publish(TOPIC_HOME_FLY_CMND_DIMMER, 100)
        # default state
        self.displayState = DISPLAY_STATE_CLOCK
        if (self.meteoHoldOption):
            self.displayState = DISPLAY_STATE_METEO
            self.mqtt.mqtt_publish(TOPIC_HOME_FLY_CMND_DISPLAY_TEXT, self.meteoText)
        else:
            # power meter time range
            if ((self.now_is_between("18:00:00", "22:00:00") or
                 self.now_is_between("05:00:00", "07:00:00")) and
                    weekday in [1, 2, 3, 4, 5]):
                self.displayState = DISPLAY_STATE_POWER_METER
            if ((self.now_is_between("05:00:00", "23:00:00")) and
                    weekday in [6, 7]):
                self.displayState = DISPLAY_STATE_POWER_METER
        #
        # timed actions
        #
        if (self.displayState == DISPLAY_STATE_CLOCK):
            self.mqtt.mqtt_publish(TOPIC_HOME_FLY_CMND_DISPLAY_CLOCK, 2)
        elif (self.displayState == DISPLAY_STATE_POWER_METER):
            pass
        elif (self.displayState == DISPLAY_STATE_METEO):
            pass
        elif (self.displayState == DISPLAY_STATE_BOILER):
            pass
        else:
            self.displayState = DISPLAY_STATE_CLOCK

    def powerMeterEvent(self, event_name, data, *args, **kwargs):
        if (self.displayState == DISPLAY_STATE_POWER_METER):
            self.totalW = data['new_state']['state']
            self.mqtt.mqtt_publish(TOPIC_HOME_FLY_CMND_DISPLAY_TEXT, self.totalW)

    def meteoEvent(self, event_name, data, *args, **kwargs):
        self.meteoText = METEO_TEXT[data['new_state']['state']]
        self.mqtt.mqtt_publish(TOPIC_HOME_FLY_CMND_DISPLAY_TEXT, self.meteoText)

