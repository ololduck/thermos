import logging
import time
from glob import glob
from signal import signal, SIGINT, SIGTERM

from RPi import GPIO

logger = logging.getLogger()


class ThermosActuator(object):
    def __init__(self, config):
        self.relay_pin = config['relay_pin']
        self.config = config
        self.should_run = True
        base_dir = '/sys/bus/w1/devices/'
        devices = glob(base_dir + '28*')
        if len(devices) < 1:
            logging.error("there doesn't seem to be a temperature probe. Are the modules loaded?")
            exit(1)
        device_folder = devices[0]
        self.device_file = device_folder + '/w1_slave'
        self.init_gpios()
        self.update_heating_status(False)
        signal(SIGINT, self.cleanup)
        signal(SIGTERM, self.cleanup)
        logger.info("Initialized thermostatd with pin %d as actuator", self.config["relay_pin"])

    def update_heating_status(self, heating):
        logger.debug("Setting heating to %s", heating)
        # The relay is active low....
        GPIO.output(self.relay_pin, not heating)

    def read_temp(self):
        def read_temp_raw(device_file):
            f = open(device_file, 'r')
            _lines = f.readlines()
            f.close()
            return _lines

        lines = read_temp_raw(self.device_file)
        while lines[0].strip()[-3:] != 'YES':
            time.sleep(0.2)
            lines = read_temp_raw()
        equals_pos = lines[1].find('t=')
        if equals_pos != -1:
            temp_string = lines[1][equals_pos + 2:]
            temp_c = float(temp_string) / 1000.0
            return temp_c
        logger.exception("could not read temperature from the probe! could not find the string 't='.")

    def run(self):
        try:
            while self.should_run:
                scheduled_temp = self.config.get_current_scheduled_temperature()
                temp = self.read_temp()
                logger.debug("scheduled/current temp are %.2f/%.2f", scheduled_temp, temp)
                if temp < scheduled_temp - self.config['threshold']:
                    heating = True
                elif temp > scheduled_temp + self.config["threshold"]:
                    heating = False
                self.update_heating_status(heating)
                time.sleep(10.0)
        finally:
            self.cleanup()

    def init_gpios(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.config['relay_pin'], GPIO.OUT)

    # Graceful exit
    def cleanup(self, signum=None, frame=None):
        self.should_run = False
        GPIO.cleanup()
