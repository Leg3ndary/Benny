class BotConfig:
    """
    Represents the bot part of config
    """
    prefix: str
    token: str
    dev_token: str
    secret: str
    webhook: str

class MongoConfig:
    """
    Represents the mongo part of config
    """
    user: str
    uri: str
    password: str

class Config:
    """
    Reads a config file to setup basic properties that the bot might need.
    """
    path: str

    def __init__(self, path: str) -> None:
        """
        Init for the config file
        """
        self.path = path