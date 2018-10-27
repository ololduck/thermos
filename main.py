# -*- coding: utf-8 -*-
import logging
from argparse import ArgumentParser

from thermos import Config
from thermos.core import ThermosActuator

logger = logging.getLogger()
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)


def main():
    parser = ArgumentParser()
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

    actuator = ThermosActuator(config)
    actuator.run()


if __name__ == "__main__":
    main()
