import logging
import time
from datetime import datetime
from glob import glob
from signal import SIGINT, SIGTERM, signal

from RPi import GPIO
from influxdb import InfluxDBClient

from thermos import Config

logger = logging.getLogger()


class ThermosActuator(object):
    """Manipulates the relay according to recorded temperatures"""

    def __init__(self, config: Config):
        """
        Args:
            config: an instance of config.Config
        """
        self.relay_pin = int(config['relay_pin'])
        self.config = config
        self.should_run = True
        self.client = InfluxDBClient(host=config.get("influxdb.host", 'localhost'),
                                     port=config.get('influxdb.port', 8086),
                                     database="thermos")
        base_dir = '/sys/bus/w1/devices/'
        devices = glob(base_dir + '28*')
        if len(devices) < 1:
            logging.error("there doesn't seem to be a temperature probe. Are the modules loaded?")
            exit(1)
        device_folder = devices[0]
        self.device_file = device_folder + '/w1_slave'
        self.init_gpios()
        self._update_heating_status(False)
        signal(SIGINT, self.cleanup)
        signal(SIGTERM, self.cleanup)
        logger.info("Initialized thermostatd with pin %d as actuator", self.config["relay_pin"])

    def _update_heating_status(self, heating: bool):
        """
        Sets the relay pin according to the boolean heating
        """
        logger.debug("Setting heating to %s", heating)
        # The relay is active low....
        GPIO.output(self.relay_pin, not heating)

    def _read_temp(self):
        """
        returns the current temperature as measured by the probe, in C°
        """

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

    def _update_influx(self, temp, measurement='actual'):
        data = {
            'measurement': measurement,
            'time': datetime.now(),
            'fields': {
                'temperature': temp
            }
        }
        logger.debug('sending to influx the following data: %s', data)
        self.client.write_points([data])

    def run(self):
        """Launches the mainloop"""
        heating = False
        try:
            while self.should_run:
                scheduled_temp = self.config.get_current_scheduled_temperature()
                temp = self._read_temp()
                logger.debug("scheduled/current temp are %.2f/%.2f", scheduled_temp, temp)
                self._update_influx(temp)
                self._update_influx(scheduled_temp, 'scheduled')
                if temp < scheduled_temp - self.config['threshold']:
                    heating = True
                elif temp > scheduled_temp + self.config["threshold"]:
                    heating = False
                self._update_heating_status(heating)
                time.sleep(10.0)
        finally:
            self.cleanup()

    def init_gpios(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.config['relay_pin'], GPIO.OUT)

    # Graceful exit
    def cleanup(self, signum=None, frame=None):
        """
        Provides a way to cleanly exit the main loop
        """
        self.should_run = False
        GPIO.cleanup()
