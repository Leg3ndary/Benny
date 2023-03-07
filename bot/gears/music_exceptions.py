"""
Music Exceptions
"""


class MusicException(Exception):
    """
    Music exception meh
    """


class QueueFull(MusicException):
    """
    When the queue is full
    """


class QueueEmpty(MusicException):
    """
    When the queue is empty
    """


class NothingPlaying(MusicException):
    """
    When nothings playing
    """


class NotConnected(MusicException):
    """
    When you are not connected to a voice channel
    """


class PlaylistException(Exception):
    """
    Raised when a playlist related method has failed
    """


class PlaylistLimitReached(PlaylistException):
    """
    Raised when the max amount of playlists has been made
    """


class PlaylistNotFound(PlaylistException):
    """
    Raised when a playlist wasn't found when querying
    """


class PlaylistSongLimitReached(PlaylistException):
    """
    Raised when a playlist has reached the max amount of songs possible
    """


class SongException(Exception):
    """
    Raised when a song related method has failed
    """


class SongnameLimitReached(SongException):
    """
    Raised when a song name is too long
    """
