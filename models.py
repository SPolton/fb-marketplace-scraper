"""Models and Constants"""

from enum import Enum


# TODO - Add more cities to the dictionary.
CITIES = [
    "nyc",
    "la",
    "vegas",
    "chicago",
    "houston",
    "sanantonio",
    "miami",
    "orlando",
    "sandiego",
    "arlington",
    "baltimore",
    "cincinnati",
    "denver",
    "fortworth",
    "jacksonville",
    "memphis",
    "nashville",
    "philly",
    "portland",
    "sanjose",
    "tucson",
    "atlanta",
    "boston",
    "columbus",
    "detroit",
    "honolulu",
    "kansascity",
    "neworleans",
    "phoenix",
    "seattle",
    "dc",
    "milwaukee",
    "sac",
    "austin",
    "charlotte",
    "dallas",
    "elpaso",
    "indianapolis",
    "louisville",
    "minneapolis",
    "oklahoma",
    "pittsburgh",
    "sanfrancisco",
    "tampa",
]
MARKETPLACE_URL = (
    "https://www.facebook.com/marketplace/{0}/search/?query={1}&maxPrice={2}"
)
INITIAL_URL = "https://www.facebook.com/login/device-based/regular/login/"


class FBClassBullshit(Enum):
    """Where to find these elements in the HTML"""

    IMAGE = "xt7dq6l xl1xv1r x6ikm8r x10wlt62 xh8yej3"
    LISTINGS = (
        "x9f619 x78zum5 x1r8uery xdt5ytf x1iyjqo2 xs83m0k x1e558r4 x150jy0e x1iorvi4 "
        "xjkvuk6 xnpuxes x291uyu x1uepa24"
    )
    TITLE = "x1lliihq x6ikm8r x10wlt62 x1n2onr6"
    PRICE = (
        "x193iq5w xeuugli x13faqbe x1vvkbs x1xmvt09 x1lliihq x1s928wv xhkezso x1gmr53x "
        "x1cpjm7i x1fgarty x1943h6x xudqn12 x676frb x1lkfr7t x1lbecb7 x1s688f xzsf02u"
    )
    URL = (
        "x1i10hfl xjbqb8w x1ejq31n xd10rxx x1sy0etr x17r0tee x972fbf xcfux6l x1qhh985 "
        "xm0m39n x9f619 x1ypdohk xt0psk2 xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r "
        "xexx8yu x4uap5 x18d9i69 xkhd6sd x16tdsg8 xggy1nq x1a2a7pz x1heor9g xt0b8zv "
        "x1hl2dhg x1lku1pv"
    )
    LOCATION = "x1lliihq x6ikm8r x10wlt62 x1n2onr6 xlyipyv xuxw1ft x1j85h84"
