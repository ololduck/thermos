import toml


class Config(dict):
    @staticmethod
    def load(config_file="thermos.toml"):
        with open(config_file) as f:
            return toml.load(f, _dict=Config)
