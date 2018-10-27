from datetime import datetime

import toml


class Config(dict):
    @staticmethod
    def load(config_file="thermos.toml"):
        with open(config_file) as f:
            return toml.load(f, _dict=Config)

    def get_current_scheduled_temperature(self) -> float:
        now = datetime.now()
        hour = now.hour
        minutes = now.minute
        if minutes > 30:  # we only handle 30 minutes slices
            minutes = 30
        else:
            minutes = 0
        return self["schedule"]["hourly"]["{:0>2d}:{:0>2d}".format(hour, minutes)]
