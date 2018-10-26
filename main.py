# -*- coding: utf-8 -*-
import glob
import logging
import time
from argparse import ArgumentParser
from datetime import datetime
from signal import SIGINT, signal, SIGTERM

import RPi.GPIO as GPIO

from thermos import Config

RELAY_PIN = 17

logging.basicConfig(level=logging.INFO)

# stolen from:
#  https://cdn-learn.adafruit.com/downloads/pdf/adafruits-raspberry-pi-lesson-11-ds18b20-temperature-sensing.pdf
# We don't need to modprobe, that should be the os's job
# os.system('modprobe w1-gpio')
# os.system('modprobe w1-therm')

base_dir = '/sys/bus/w1/devices/'
devices = glob.glob(base_dir + '28*')
if len(devices) < 1:
    logging.error("there doesn't seem to be a temperature probe. Are the modules loaded?")
    exit(1)
device_folder = devices[0]
device_file = device_folder + '/w1_slave'

parser = ArgumentParser()

should_run = True


# Graceful exit
def cleanup(signum=None, frame=None):
    global should_run
    should_run = False
    GPIO.output(RELAY_PIN, False)
    GPIO.cleanup()


signal(SIGINT, cleanup)
signal(SIGTERM, cleanup)


def read_temp():
    def read_temp_raw():
        f = open(device_file, 'r')
        _lines = f.readlines()
        f.close()
        return _lines

    lines = read_temp_raw()
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw()
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos + 2:]
        temp_c = float(temp_string) / 1000.0
        return temp_c


def update_heating_status(heating):
    logging.debug("Setting heating to %s", heating)
    # The relay is active low....
    GPIO.output(RELAY_PIN, not heating)


def main():
    parser.add_argument("--threshold", type=float, default=0.5,
                        help="how many C° should we allow from the target temperature")
    parser.add_argument("-c", "--config", help="path to the configuration file to use", default="thermos.toml")
    args = vars(parser.parse_args())
    logging.debug(args)

    logging.info("Loading config file %s...", args["config"])
    config = Config.load(args["config"])

    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(RELAY_PIN, GPIO.OUT)
        GPIO.output(RELAY_PIN, GPIO.LOW)
        heating = False
        logging.info("Initialized thermostatd with pin %d as actuator", RELAY_PIN)
        while should_run:
            now = datetime.now()
            hour = now.hour
            minutes = now.minute
            if minutes > 30:  # we only handle 30 minutes slices
                minutes = 30
            current_scheduled_temperature = config["schedule"]["hourly"]["{:0>2d}:{:0>2d}".format(hour, minutes)]
            temp = read_temp()
            logging.debug("Current temp is %d", temp)
            if temp < current_scheduled_temperature - args['threshold']:
                heating = True
            elif temp > current_scheduled_temperature + args["threshold"]:
                heating = False
            update_heating_status(heating)
            time.sleep(10.0)

    except KeyboardInterrupt:
        logging.info("Program interrupted by user.")
    finally:
        cleanup()


if __name__ == "__main__":
    main()
