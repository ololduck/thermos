import toml
from datetime import datetime
from logging import getLogger

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
        """Persists the configuration on disk"""
        if self.config_file is None:
            logger.exception("self.config_file is not defined! that should definitely not happen.")
        with open(self.config_file, "w+") as f:
            toml.dump(self, f)

    def get_current_scheduled_temperature(self):
        """Returns the current (according to datetime.now()) temperature we should have"""
        now = datetime.now()
        hour = now.hour
        minutes = now.minute
        if minutes > 30:  # we only handle 30 minutes slices
            minutes = 30
        else:
            minutes = 0
        return self["schedule"]["hourly"]["{:0>2d}:{:0>2d}".format(hour, minutes)]

    def get(self, k, default=None):
        """
        returns the value specified by :param k:, where k uses dot-syntax to access fields. See examples
        :param k: key
        :param default: a default value to return if nothing is found


        >>> d = Config()
        >>> d["influx"] = {"host": "localhost", "port": 8081}
        >>> d.get("influx.host")
        'localhost'
        >>> d.get("does.not.exist", None)
        >>> d.get("influx")
        {'host': 'localhost', 'port': 8081}
        """
        if '.' in k:
            v = self.get(k.split('.')[0], default)
            if v == default:
                return default
            return v.get(".".join(k.split('.')[1:])) or default
        return super(Config, self).get(k, default) or default
