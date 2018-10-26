# -*- coding: utf-8 -*-
import glob
import time
from argparse import ArgumentParser

import RPi.GPIO as GPIO

RELAY_PIN=17


# stolen from:
#  https://cdn-learn.adafruit.com/downloads/pdf/adafruits-raspberry-pi-lesson-11-ds18b20-temperature-sensing.pdf
# We don't need to modprobe, that should be the os's job
# os.system('modprobe w1-gpio')
# os.system('modprobe w1-therm')
base_dir = '/sys/bus/w1/devices/'
devices = glob.glob(base_dir + '28*')
if len(devices) < 1:
    print("there doesn't seem to be a temperature probe. Are the modules loaded?")
device_folder = devices[0]
device_file = device_folder + '/w1_slave'

parser = ArgumentParser()


def read_temp():
    def read_temp_raw():
        f = open(device_file, 'r')
        lines = f.readlines()
        f.close()
        return lines

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
    print("Setting {} to {}".format(RELAY_PIN, heating))
    # The relay is active low....
    GPIO.output(RELAY_PIN, not heating)


def main():
    print("in Main")
    parser.add_argument("-t", "--target-temp", type=float, required=True, help="Target temperature")
    parser.add_argument("--threshold", type=float, default=1.0,
                        help="how many C° should we allow from the target temperature")
    args = vars(parser.parse_args())
    print(args)

    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(RELAY_PIN, GPIO.OUT)
        GPIO.output(RELAY_PIN, GPIO.LOW)
        heating = False
        while True:
            temp = read_temp()
            print("Current temp is %d", temp)
            if temp < args['target_temp']:
                heating = True
            elif temp > args['target_temp'] + args["threshold"]:
                heating = False

            update_heating_status(heating)

            time.sleep(10.0)
    except KeyboardInterrupt:
        GPIO.output(RELAY_PIN, False)
        GPIO.cleanup()
        print("Program interrupted by user.")


if __name__ == "__main__":
    main()
