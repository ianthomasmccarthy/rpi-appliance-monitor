from telegram_send import send
from threading import Thread

import traceback
import logging
import datetime
import RPi.GPIO
# import json
# import sys
import time


class LaundryMassager(object):
    """Uses a Vibration sensor to keep track of the dryer."""

    def __init__(self):
        self.sensor_pin       = 14  # Default Sensor pin is 14
        self.s_vib_time       = 0
        self.l_vib_time       = 0
        self.appliance_active = False
        self.active_message   = "Dryer has started."
        self.stopped_message  = "Dryer has Stopped. Duration {t} minutes."
        self.inactive_message = "Dryer has been inactive since {t}"
        self.log_file = "/home/pi/rpi-appliance-monitor/logs/vib.log"
        self.count = 0
        self.count_thresh = 40
        self.sleep_interval = 60
        self.stopped = 0
        self.stopped_thresh = 3
        self.inactive_thresh = 86400
        self.debug = True
        self.active = False

    def get_logger(self):
        """Get Logger."""
        self.log = logging.getLogger(__name__)
        if self.debug:
            self.log.setLevel(logging.DEBUG)
        else:
            self.log.setLevel(logging.INFO)

        handler = logging.FileHandler(self.log_file)
        handler.setLevel(logging.INFO)

        formatter = logging.Formatter('%(asctime)s - %(funcName)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.log.addHandler(handler)

    def vibrated(self, x):
        # self.log.info("Vibrated")
        self.count += 1
        if self.count < self.count_thresh:
            return
        if self.count >= self.count_thresh:
            self.count = 0  # Reset a greater than count here.
            self.l_vib_time = time.time()
            if self.active:
                self.log.debug("Vibrating but already active.")
                return
            if not self.active:
                self.log.debug("Becoming active")
                self.active = True
                self.s_vib_time = time.time()
                self.send_appliance_active()
                self.log.debug("Should have sent appliance active message")

    def spawn_monitor(self):
        t = Thread(target=self.monitor, args=())
        t.daemon = True
        t.start()
        return

    def monitor(self):
        while True:
            try:
                self.log.debug("Sleeping for {s} seconds".format(s=self.sleep_interval))
                time.sleep(self.sleep_interval)
                if self.active:
                    if self.count < self.count_thresh:
                        self.stopped += 1
                        if self.stopped >= self.stopped_thresh:
                            tot_time = time.time() - self.s_vib_time / 60
                            self.send_appliance_stopped(duration=tot_time)
                else:
                    if self.l_vib_time > self.inactive_thresh:
                        self.send_appliance_inactive()
                        self.l_vib_time = time.time()
            except Exception as e:
                raise e

    def convert_timestamp(ts):
        """Return a string of datetime from a time.time() timestamp."""
        return str(datetime.datetime.fromtimestamp(ts).strftime('%c'))

    def send_appliance_active(self):
        self.send_alert(message=self.active_message)

    def send_appliance_stopped(self, duration):
        self.send_alert(message=self.stopped_message.format(t=duration))

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
        except Exception as e:
            tb = traceback.format_exc()
            self.log.error("Problem setting up gpio pin monitoring. e:{e}; tb:{tb}".format(e=e, tb=tb))
        else:
            self.log.info("Monitoring GPIO pin #{n} Setup Successfully.".format(n=str(sensor_pin)))

    def main(self):
        self.get_logger()
        self.gpio_setup(sensor_pin=self.sensor_pin)
        self.spawn_monitor()
        while True:
            time.sleep(1)

if __name__ == '__main__':
    lm = LaundryMassager()
    lm.main()
