"""
Custom Module to house the bot style related information
"""

import random

__all__ = ("Color", "Emoji")


class Color:
    """
    Our base colors
    """

    NAVY = 0x001F3F
    BLUE = 0x0074D9
    AQUA = 0x7FDBFF
    TEAL = 0x39CCCC
    OLIVE = 0x3D9970
    GREEN = 0x2ECC40
    LIME = 0x01FF70
    YELLOW = 0xFFDC00
    ORANGE = 0xFF851B
    RED = 0xFF4136
    MAROON = 0x85144B
    PINK = 0xF012BE
    PURPLE = 0xB10DC9
    BLACK = 0x111111
    GRAY = 0xAAAAAA
    GREY = 0xAAAAAA
    SILVER = 0xDDDDDD
    WHITE = 0xFFFFFF

    @classmethod
    def random(cls) -> hex:
        """
        Return a random hex
        """
        colors = {
            "navy": 0x001F3F,
            "blue": 0x0074D9,
            "aqua": 0x7FDBFF,
            "teal": 0x39CCCC,
            "olive": 0x3D9970,
            "green": 0x2ECC40,
            "lime": 0x01FF70,
            "yellow": 0xFFDC00,
            "orange": 0xFF851B,
            "red": 0xFF4136,
            "maroon": 0x85144B,
            "pink": 0xF012BE,
            "purple": 0xB10DC9,
            "black": 0x111111,
            "gray": 0xAAAAAA,
            "grey": 0xAAAAAA,
            "silver": 0xDDDDDD,
            "white": 0xFFFFFF,
        }
        return random.choice(list(colors.values()))


class RegularEmoji:
    """
    Regular emoji class
    """

    check = "<:_:891088754176036885>"
    cancel = "<:_:891088754599682059>"
    left = "<:_:923972333360775228>"
    right = "<:_:923972333461458944>"
    pauseplay = "<:_:923972333599866912>"
    stop = "<:_:923972333885091860>"
    search = "<:_:923972333742469130>"
    loop = "<:_:923972333343997962>"
    shuffle = "<:_:923972333612433548>"
    spotify = "<:_:922245976226402306>"
    soundcloud = "<:_:927006460834111518>"
    youtube = "<:_:927005602964729887>"
    music = "<:_:1030661483400548432>"


class IDEmoji:
    """
    Emojis ID's
    """

    check = "891088754176036885"
    cancel = "891088754599682059"
    left = "923972333360775228"
    right = "923972333461458944"
    pauseplay = "923972333599866912"
    stop = "923972333885091860"
    search = "923972333742469130"
    loop = "923972333343997962"
    shuffle = "923972333612433548"
    spotify = "922245976226402306"
    soundcloud = "927006460834111518"
    youtube = "927005602964729887"
    music = "1030661483400548432"


class ImageEmoji:
    """
    Image urls for all our emojis
    """

    check = "https://cdn.discordapp.com/emojis/891088754176036885.png?size=256"
    cancel = "https://cdn.discordapp.com/emojis/891088754599682059.png?size=256"
    left = "https://cdn.discordapp.com/emojis/923972333360775228.png?size=256"
    right = "https://cdn.discordapp.com/emojis/923972333461458944.png?size=256"
    pauseplay = "https://cdn.discordapp.com/emojis/923972333599866912.png?size=256"
    stop = "https://cdn.discordapp.com/emojis/923972333885091860.png?size=256"
    search = "https://cdn.discordapp.com/emojis/923972333742469130.png?size=256"
    loop = "https://cdn.discordapp.com/emojis/923972333343997962.png?size=256"
    shuffle = "https://cdn.discordapp.com/emojis/923972333612433548?size=256"
    spotify = "https://cdn.discordapp.com/emojis/922245976226402306.png?size=256"
    soundcloud = "https://cdn.discordapp.com/emojis/927006460834111518?size=256"
    youtube = "https://cdn.discordapp.com/emojis/927005602964729887?size=256"
    music = "https://cdn.discordapp.com/emojis/1030661483400548432?size=256"


class Emoji:
    """
    Base class for all emojis
    """

    REGULAR = RegularEmoji
    ID = IDEmoji
    IMAGE = ImageEmoji
