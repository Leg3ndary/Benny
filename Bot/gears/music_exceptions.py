class MusicException(Exception):
    """Music exception meh"""

    pass


class QueueFull(MusicException):
    """When the queue is full"""

    pass


class QueueEmpty(MusicException):
    """When the queue is empty"""

    pass


class NothingPlaying(MusicException):
    """When nothings playing"""

    pass


class PlaylistException(Exception):
    """
    Raised when a playlist related method has failed
    """

    pass


class PlaylistLimitReached(PlaylistException):
    """
    Raised when the max amount of playlists has been made
    """

    pass


class PlaylistNotFound(PlaylistException):
    """
    Raised when a playlist wasn't found when querying
    """

    pass


class PlaylistSongLimitReached(PlaylistException):
    """
    Raised when a playlist has reached the max amount of songs possible
    """

    pass


class SongException(Exception):
    """
    Raised when a song related method has failed
    """

    pass


class SongnameLimitReached(SongException):
    """
    Raised when a song name is too long
    """

    pass
