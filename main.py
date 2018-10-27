# -*- coding: utf-8 -*-
import glob
import logging
import time
from argparse import ArgumentParser
from signal import SIGINT, signal, SIGTERM

import RPi.GPIO as GPIO

from thermos import Config
from thermos.utils import init_gpios

RELAY_PIN = 17

logger = logging.getLogger()
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)

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
    logger.debug("Setting heating to %s", heating)
    # The relay is active low....
    GPIO.output(RELAY_PIN, not heating)


def main():
    parser.add_argument("--threshold", type=float, default=0.5,
                        help="how many C° should we allow from the target temperature")
    parser.add_argument("-c", "--config", help="path to the configuration file to use", default="thermos.toml")
    parser.add_argument("--relay-pin", type=int, required=False, help="On which GPIO pin is the relay command input")
    parser.add_argument("-v", "--verbose", action="count", default=0,
                        help="Increase verbosity. Can be repeated.")
    args = vars(parser.parse_args())
    logger.setLevel(logging.INFO - args["verbose"] * 10)
    logger.debug(args)

    logger.info("Loading config file %s...", args["config"])
    config = Config.load(args["config"])
    config.update(**args)

    try:
        init_gpios(config)
        heating = False
        update_heating_status(heating)
        logger.info("Initialized thermostatd with pin %d as actuator", config["relay_pin"])
        while should_run:
            scheduled_temp = config.get_current_scheduled_temperature()
            temp = read_temp()
            logger.debug("scheduled/current temp are %.2f/%.2f", scheduled_temp, temp)
            if temp < scheduled_temp - args['threshold']:
                heating = True
            elif temp > scheduled_temp + args["threshold"]:
                heating = False
            update_heating_status(heating)
            time.sleep(10.0)

    except KeyboardInterrupt:
        logger.info("Program interrupted by user.")
    finally:
        cleanup()


if __name__ == "__main__":
    main()
