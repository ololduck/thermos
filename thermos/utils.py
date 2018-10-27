from RPi import GPIO


def init_gpios(config):
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(config['relay_pin'], GPIO.OUT)
