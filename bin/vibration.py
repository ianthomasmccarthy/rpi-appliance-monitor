from telegram_send import send

import traceback
import logging
import datetime
import RPi.GPIO
import time


class LaundryMassager(object):
    """Uses a Vibration sensor to keep track of the dryer."""

    def __init__(self):
        """Constructor."""
        self.active_message = "Dryer has started."
        self.stopped_message = "Dryer has Stopped. Duration {t} minutes."
        self.inactive_message = "Dryer has been inactive since {t}"
        self.log_file = "/home/pi/rpi-appliance-monitor/logs/vib.log"
        self.log = None
        self.debug = True
        self.appliance_active = False
        self.sensor_pin = 14  # Default Sensor pin is 14
        self.s_vib_time = 0
        self.l_vib_time = time.time()
        self.count = 0
        self.count_thresh = 20  # How many times it has to vib to not be a false positive
        self.sleep_interval = 20
        self.inactive_thresh = 86400  # Counting a full day between last vib before sending inactive message
        self.stopped_thresh = 120  # after 120 seconds will it consider it really stopped.

    def get_logger(self):
        """Get Logger."""
        self.log = logging.getLogger(__name__)
        if self.debug:
            self.log.setLevel(logging.DEBUG)
        else:
            self.log.setLevel(logging.INFO)
        handler = logging.FileHandler(self.log_file)
        formatter = logging.Formatter('%(asctime)s - %(funcName)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.log.addHandler(handler)

    def vibrated(self, x):
        self.log.debug("Vibrated callback.")
        self.count += 1
        self.l_vib_time = int(time.time())

    @staticmethod
    def convert_timestamp(ts):
        """Return a string of datetime from a time.time() timestamp."""
        try:
            retval = str(datetime.datetime.fromtimestamp(ts).strftime('%c'))
        except Exception as e:
            retval = "Date Error"
        finally:
            return retval

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

    def start_active(self):
        now = int(time.time())
        self.appliance_active = True
        self.s_vib_time = now
        self.log.info("Sending Appliance Active Message.")
        self.send_appliance_active()

    def should_stop(self):
        now = int(time.time())
        if (int(now) - int(self.l_vib_time)) > self.stopped_thresh:
            self.appliance_active = False
            tot_time = int(now) - int(self.s_vib_time) / 60
            self.log.info("Sending Appliance Stopping Message. Duration was {d}".format(d=tot_time))
            self.send_appliance_stopped(duration=tot_time)
            self.reset()

    def reset(self):
        self.s_vib_time = 0

    def inactive_check(self):
        now = int(time.time())
        if (now - self.l_vib_time) > self.inactive_thresh:
            self.log.info("Sending Appliance Inactive Message.")
            self.send_appliance_inactive()
            self.l_vib_time = now


    def main(self):
        self.get_logger()
        self.gpio_setup(sensor_pin=self.sensor_pin)
        while True:
            self.count = 0
            time.sleep(self.sleep_interval)
            try:
                self.log.debug("Count was {c}".format(c=self.count))
                if self.count >= self.count_thresh:
                    if self.appliance_active:
                        continue
                    else:
                        self.start_active()
                        continue
                else:
                    if self.appliance_active:
                        self.should_stop()
                        continue
                    else:
                        self.inactive_check()
                    continue
            except Exception as e:
                self.log.error("General Issue: e:{e}".format(e=e))

if __name__ == '__main__':
    lm = LaundryMassager()
    lm.main()
