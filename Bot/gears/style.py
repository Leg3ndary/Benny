import random


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
    def random(self) -> hex:
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


reversed_colors = {
    7999: "navy",
    29913: "blue",
    8379391: "aqua",
    3787980: "teal",
    4036976: "olive",
    3066944: "green",
    130928: "lime",
    16768000: "yellow",
    16745755: "orange",
    16728374: "red",
    8721483: "maroon",
    15733438: "pink",
    11603401: "purple",
    1118481: "black",
    11184810: "gray",
    14540253: "silver",
    16777215: "white",
}


color_list = [
    "navy",
    "blue",
    "aqua",
    "teal",
    "olive",
    "green",
    "lime",
    "yellow",
    "orange",
    "red",
    "maroon",
    "pink",
    "purple",
    "black",
    "gray",
    "silver",
    "white",
]


class RegularEmojis:
    """
    Regular emoji class
    """
    check = "<:check:891088754176036885>"
    cancel = "<:cancel:891088754599682059>"
    left = "<:left:923972333360775228>"
    right = "<:right:923972333461458944>"
    pauseplay = "<:pp:923972333599866912>"
    stop = "<:stop:923972333885091860>"
    search = "<:search:923972333742469130>"
    loop = "<:loop:923972333343997962>"
    shuffle = "<:shuffle:923972333612433548>"
    spotify = "<:spotify:922245976226402306>"
    soundcloud = "<:soundcloud:927006460834111518>"
    youtube = "<:youtube:927005602964729887>"

class IDEmojis:
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

class ImageEmojis:
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

class Emojis:
    """
    Base class for all emojis
    """
    REGULAR = RegularEmojis
    ID = IDEmojis
    IMAGE = ImageEmojis
