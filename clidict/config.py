"""URLs, HTTP headers, and Rich style constants."""

from rich.style import Style

BASE_URL = "https://dictionary.cambridge.org"
ENTRY_URL = BASE_URL + "/zhs/词典/英语-汉语-简体/{word}"
ENTRY_URL_EN = BASE_URL + "/zhs/词典/英语/{word}"

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36"
)

HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

STYLE_WORD = Style(color="cyan", bold=True)
STYLE_POS = Style(color="bright_black", italic=True)
STYLE_UK = Style(color="red")
STYLE_US = Style(color="blue")
STYLE_IPA = Style(color="yellow")
STYLE_LEVEL = Style(color="green", bold=True)
STYLE_GRAMMAR = Style(color="bright_black")
STYLE_PHRASE = Style(color="cyan", bold=True)
STYLE_USAGE = Style(color="magenta", italic=True)
STYLE_DEF_EN = Style(color="white")
STYLE_DEF_ZH = Style(color="bright_yellow")
STYLE_EX_EN = Style(color="bright_black")
STYLE_EX_ZH = Style(color="yellow")
STYLE_BULLET = Style(color="cyan")
STYLE_INDEX = Style(color="cyan", bold=True)

# ── 千亿词霸 (Russian-Chinese) styles ───────────────────────────
STYLE_RU_WORD = Style(color="bright_cyan", bold=True)
STYLE_STRESS = Style(color="yellow", bold=True)
STYLE_RU_DEF = Style(color="bright_yellow")
STYLE_RU_EX_ZH = Style(color="bright_black")
STYLE_RU_EX_RU = Style(color="white")
STYLE_SECTION = Style(color="cyan", bold=True)
STYLE_FIELD = Style(color="magenta")
STYLE_TABLE_HDR = Style(color="green", bold=True)
STYLE_TABLE_ROW = Style(color="bright_black")
STYLE_ERROR = Style(color="red", bold=True)
