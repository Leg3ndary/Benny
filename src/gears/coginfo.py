from useful import len_file


class CogInfo:
    """Cog Info class I can use to get and add more information to a cog easily"""

    def __init__(self, official: str, file: str, version: float, description: str):
        """
        Official - Official Name
        File - Filename
        Version - Version Number
        Description - Description of Cog
        Lines - How many lines it took to write this cog
        """
        self.official = official
        self.file = file
        self.version = version
        self.description = description
        self.line = len_file(file)
