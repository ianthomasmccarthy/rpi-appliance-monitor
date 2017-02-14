from telegram_send import send
from threading import Thread

import traceback
import logging
import datetime
import RPi.GPIO
import requests
import json
import sys
import time


class LaundryMassager(object):
    """Uses a Vibration sensor to keep track of the dryer."""

    def __init__(self):
        self.sensor_pin       = 14  # Default Sensor pin is 14
        self.s_vib_time       = 0
        self.l_vib_time       = 0
        self.appliance_active = False
        self.active_message   = "Dryer has started."
        self.stopped_message  = "Dryer has Stopped."
        self.inactive_message = "Dryer has been inactive since {t}"
        self.log_file = "/home/pi/projects/vib.log"
        self.count = 0
        self.count_thresh = 40

    def get_logger(self):
        """Get Logger."""
        self.log = logging.getLogger(__name__)
        self.log.setLevel(logging.INFO)

        handler = logging.FileHandler(self.log_file)
        handler.setLevel(logging.INFO)

        formatter = logging.Formatter('%(asctime)s - %(funcName)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.log.addHandler(handler)

    def vibrated(self, x):
        #self.log.info("Vibrated")
        self.count += 1
        if self.count >= self.count_thresh:
            self.log.info("Vibrated {c} times.".format(c=self.count))
            self.count = 0

    def convert_timestamp(ts):
        """Return a string of datetime from a time.time() timestamp."""
        return str(datetime.datetime.fromtimestamp(ts).strftime('%c'))

    def send_appliance_active(self):
        self.send_alert(message=self.active_message)

    def send_appliance_stopped(self):
        self.send_alert(message=self.stopped_message)

    def send_appliance_inactive(self):
        self.send_alert(message=self.inactive_message.format(t=self.convert_timestamp(ts=self.l_vib_time)))

    def send_alert(self, message):
        mlist = []
        mlist.append(message)
        try:
            send(messages=mlist)
        except Exception as e:
            tb = traceback.format_exc()
            self.log.error("Problem with sending telegram message. e:{e}; tb:{tb}".format(e=e, tb=tb))

    def gpio_setup(self, sensor_pin):
        try:
            RPi.GPIO.setwarnings(False)
            RPi.GPIO.setmode(RPi.GPIO.BCM)
            RPi.GPIO.setup(sensor_pin, RPi.GPIO.IN, pull_up_down=RPi.GPIO.PUD_DOWN)
            RPi.GPIO.add_event_detect(sensor_pin, RPi.GPIO.RISING, callback=self.vibrated, bouncetime=1)
            #RPi.GPIO.add_event_callback(sensor_pin, self.vibrated)
        except Exception as e:
            tb = traceback.format_exc()
            self.log.error("Problem setting up gpio pin monitoring. e:{e}; tb:{tb}".format(e=e, tb=tb))
        else:
            self.log.info("Monitoring GPIO pin #{n} Setup Successfully.".format(n=str(sensor_pin)))

    def main(self):
        self.get_logger()
        self.gpio_setup(sensor_pin=self.sensor_pin)
        while True:
            time.sleep(1)

if __name__ == '__main__':
   lm = LaundryMassager()
   lm.main()
