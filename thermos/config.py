from datetime import datetime
from logging import getLogger

import toml

logger = getLogger()


class Config(dict):
    @staticmethod
    def load(config_file="thermos.toml"):
        with open(config_file) as f:
            config = toml.load(f, _dict=Config)
        config.config_file = config_file
        return config

    def __init__(self, *args, **kwargs):
        self.config_file = None
        super(Config, self).__init__(*args, **kwargs)

    def save(self):
        if self.config_file is None:
            logger.exception("self.config_file is not defined! that should definitely not happen.")
        with open(self.config_file, "w+") as f:
            toml.dump(self, f)

    def get_current_scheduled_temperature(self) -> float:
        now = datetime.now()
        hour = now.hour
        minutes = now.minute
        if minutes > 30:  # we only handle 30 minutes slices
            minutes = 30
        else:
            minutes = 0
        return self["schedule"]["hourly"]["{:0>2d}:{:0>2d}".format(hour, minutes)]
