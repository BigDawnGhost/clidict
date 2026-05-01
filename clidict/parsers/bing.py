"""Bing Dictionary (cn.bing.com/dict) parser — Cambridge fallback.

Uses server-rendered HTML (``_EDGE_S=mkt=zh-cn`` cookie required for
Chinese content from non-China IPs).  Only the static portions are
available — authoritative definitions with examples are JS-rendered.
"""

import re

from lxml import html

from clidict.config import HEADERS
from clidict.http import fetch

SEARCH_URL = "https://cn.bing.com/dict/search?q={word}"
BING_COOKIES = {"_EDGE_S": "mkt=zh-cn"}


def _text(el, default: str = "") -> str:
    if el is None:
        return default
    return re.sub(r"\s+", " ", el.text_content()).strip()


def _parse_pron(raw: str) -> str:
    m = re.search(r"\[(.+?)\]", raw)
    return m.group(1) if m else ""


class BingParser:
    """Parse a Bing Dictionary entry page."""

    def __init__(self, html_content: str, word: str = ""):
        self.tree = html.fromstring(html_content)
        self.word = word.strip()

    @classmethod
    def from_url(cls, word: str, timeout: int = 10) -> "BingParser":
        from urllib.parse import quote

        url = SEARCH_URL.format(word=quote(word.strip()))
        resp = fetch(url, headers=HEADERS, cookies=BING_COOKIES, timeout=timeout)
        return cls(resp.text, word=word.strip())

    def get_headword(self) -> str:
        hw = self.tree.xpath('//div[contains(@class,"hd_div")]//strong')
        return _text(hw[0]) if hw else self.word

    def get_pronunciation(self) -> dict[str, str]:
        result: dict[str, str] = {"UK": "", "US": ""}
        us = self.tree.xpath('//div[contains(@class,"hd_prUS")]')
        uk = self.tree.xpath('//div[contains(concat(" ",@class," ")," hd_pr ")]')
        if us:
            result["US"] = _parse_pron(_text(us[0]))
        if uk:
            result["UK"] = _parse_pron(_text(uk[0]))
        return result

    def get_inflections(self) -> str:
        el = self.tree.xpath('//div[contains(@class,"hd_if")]')
        return _text(el[0]) if el else ""

    def get_pos_summary(self) -> list[dict]:
        """Return POS + short Chinese definitions from the summary <ul>."""
        items: list[dict] = []
        for li in self.tree.xpath('//ul/li[span[contains(@class,"pos")]]'):
            pos = li.xpath('.//span[contains(@class,"pos")]')
            definition = li.xpath('.//span[contains(@class,"def")]')
            items.append(
                {
                    "pos": _text(pos[0]) if pos else "",
                    "zh": _text(definition[0]) if definition else "",
                }
            )
        return items

    def parse(self) -> dict:
        return {
            "word": self.get_headword(),
            "pronunciation": self.get_pronunciation(),
            "inflections": self.get_inflections(),
            "pos_summary": self.get_pos_summary(),
        }

    def is_valid_entry(self) -> bool:
        return bool(self.tree.xpath('//div[contains(@class,"hd_div")]'))
