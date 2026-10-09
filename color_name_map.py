from typing import Optional

# Rocket League club color palette (7x15 grid), name -> hex code
COLOR_NAME_MAP: dict[str, str] = {
    "white1": "e5e5e5",
    "white2": "bfbfbf",
    "white3": "999999",
    "white4": "666666",
    "white5": "3f3f3f",
    "white6": "262626",
    "red1": "ff7f7e",
    "red2": "ff5959",
    "red3": "fb3238",
    "red4": "fa0203",
    "red5": "b20000",
    "red6": "660000",
    "orange1": "ff9f7f",
    "orange2": "ff8259",
    "orange3": "fc6634",
    "orange4": "fa4100",
    "orange5": "b42b01",
    "orange6": "661900",
    "mango1": "ffce7f",
    "mango2": "ffbf5b",
    "mango3": "ffce7f",
    "mango4": "ff9f00",
    "mango5": "b26f00",
    "mango6": "663e00",
    "yellow1": "efff7c",
    "yellow2": "e9ff56",
    "yellow3": "e6ff31",
    "yellow4": "deff00",
    "yellow5": "9ab204",
    "yellow6": "5a6500",
    "lime1": "aaff7e",
    "lime2": "95ff5a",
    "lime3": "7cff33",
    "lime4": "5eff01",
    "lime5": "41b202",
    "lime6": "236702",
    "green1": "7eff80",
    "green2": "59fe5a",
    "green3": "31ff32",
    "green4": "00ff01",
    "green5": "00b300",
    "green6": "006600",
    "teal1": "7fffb2",
    "teal2": "57ff9b",
    "teal3": "36fd89",
    "teal4": "00ff65",
    "teal5": "01b248",
    "teal6": "006627",
    "sky1": "7fe9ff",
    "sky2": "58e4ff",
    "sky3": "32ddfb",
    "sky4": "00d5ff",
    "sky5": "0094b2",
    "sky6": "015466",
    "blue1": "7fb0ff",
    "blue2": "5999fd",
    "blue3": "3083fb",
    "blue4": "0061fe",
    "blue5": "0044b1",
    "blue6": "002866",
    "navy1": "7f88ff",
    "navy2": "5764ff",
    "navy3": "3340ff",
    "navy4": "0011ff",
    "navy5": "000bb2",
    "navy6": "000666",
    "violet1": "ae7fff",
    "violet2": "9958fe",
    "violet3": "7d31ff",
    "violet4": "5b03f8",
    "violet5": "4400b0",
    "violet6": "250067",
    "purple1": "e480fe",
    "purple2": "df57ff",
    "purple3": "d135fb",
    "purple4": "d500f8",
    "purple5": "8e01b2",
    "purple6": "540066",
    "lilac1": "ff7fd1",
    "lilac2": "fd5ac3",
    "lilac3": "f935b1",
    "lilac4": "ff01a1",
    "lilac5": "b20070",
    "lilac6": "650141",
    "blood1": "ff8095",
    "blood2": "ff5973",
    "blood3": "fe3253",
    "blood4": "ff002a",
    "blood5": "b3001d",
    "blood6": "660010"
}


def get_color_hex(name: str) -> Optional[str]:
    """
    Look up a color by name (case-insensitive) and return its hex code,
    or None if the name doesn't match any known color.
    """
    return COLOR_NAME_MAP.get(name.strip().lower())


def get_all_color_hexes(text: str) -> list[str]:
    """
    Split text on '&' and look up each part as a color name.
    Returns only the hex codes that were found, skipping any unmatched names.
    """
    hexes = []
    for part in text.split("&"):
        hex_code = get_color_hex(part)
        if hex_code:
            hexes.append(hex_code)
    return hexes


def get_nice_color_content(text: str) -> str:
    """Format a complete color-code submission for display, leaving other text unchanged."""
    color_names = [part.strip() for part in text.split("&")]
    if any(get_color_hex(name) is None for name in color_names):
        return text
    return " & ".join(name.title() for name in color_names)
