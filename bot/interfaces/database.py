"""
This is just a file to help me implement a small database class
"""

import asqlite


class BennyDatabases:
    """
    Simple database class
    """

    def __init__(self) -> None:
        """
        Init the database class
        """
        self.users: asqlite.Connection = None
        self.servers: asqlite.Connection = None
