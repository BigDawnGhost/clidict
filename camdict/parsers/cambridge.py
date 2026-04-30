"""Core parser for Cambridge Dictionary (AMP) entry pages."""

import re

from lxml import html

from camdict.config import ENTRY_URL, HEADERS
from camdict.http import fetch


def _text(el, default: str = "") -> str:
    """Get cleaned text content of an lxml element."""
    if el is None:
        return default
    text = el.text_content().strip()
    return re.sub(r"\s+", " ", text)


class CambridgeParser:
    """Parse a Cambridge Dictionary (AMP) entry page with lxml."""

    _KNOWN_POS: set[str] = {
        "noun",
        "verb",
        "adjective",
        "adverb",
        "pronoun",
        "preposition",
        "conjunction",
        "interjection",
        "exclamation",
        "determiner",
        "number",
        "auxiliary",
        "modal",
        "prefix",
        "suffix",
        "predeterminer",
        "idiom",
        "phrasal verb",
        "phrase",
        "quantifier",
        "abbreviation",
    }

    _PLACEHOLDER_HW: set[str] = {"剑桥词典：英语-中文(简体)翻译", ""}

    _USAGE_LABELS: tuple[str, ...] = (
        "informal",
        "formal",
        "old-fashioned",
        "literary",
        "humorous",
        "slang",
        "approving",
        "disapproving",
        "offensive",
        "mainly uk",
        "mainly us",
    )

    def __init__(self, html_content: str, url: str = "") -> None:
        self.tree = html.fromstring(html_content)
        self.url = url

    @classmethod
    def from_url(cls, word: str, timeout: int = 10) -> "CambridgeParser":
        url = ENTRY_URL.format(word=word.strip().lower())
        resp = fetch(url, headers=HEADERS, timeout=timeout)
        return cls(resp.text, url=url)

    def get_headword(self) -> str:
        hw = self.tree.xpath('//span[contains(@class,"headword")]')
        if hw:
            return _text(hw[0])
        meta = self.tree.xpath('//meta[@property="og:title"]/@content')
        return meta[0].strip() if meta else ""

    def get_part_of_speech(self) -> str:
        pos_spans = self.tree.xpath(
            '//div[contains(@class,"pos-header")]'
            '//span[contains(@class,"pos") and contains(@class,"dpos")]'
        )
        seen: set[str] = set()
        parts: list[str] = []
        for sp in pos_spans:
            t = sp.text_content().strip().lower()
            if t in self._KNOWN_POS and t not in seen:
                seen.add(t)
                parts.append(t)
        return ", ".join(parts)

    def get_pronunciation(self) -> dict[str, str]:
        result: dict[str, str] = {"UK": "", "US": ""}
        for region, cls_prefix in (("UK", "uk"), ("US", "us")):
            span = self.tree.xpath(
                f'//span[contains(@class,"{cls_prefix}") and contains(@class,"dpron-i")]'
            )
            if span:
                pron = span[0].xpath('.//span[contains(@class,"pron")]')
                if pron:
                    result[region] = pron[0].text_content().strip()
        return result

    def get_senses(self) -> list[dict]:
        senses: list[dict] = []
        # Regular def-blocks — exclude those nested inside phrase-blocks
        xpath = (
            '//div[contains(@class,"def-block")]'
            '[not(ancestor::div[contains(@class,"phrase-block")])]'
        )
        for block in self.tree.xpath(xpath):
            sense = self._parse_def_block(block)
            if sense["definition_en"] or sense["definition_zh"]:
                senses.append(sense)
        # Phrasal verbs / idioms — listed after regular senses
        senses.extend(self._parse_phrase_blocks())
        return senses

    def _parse_def_block(self, block, phrase: str = "") -> dict:
        sense: dict = {
            "phrase": phrase,
            "level": "",
            "grammar": "",
            "usage": "",
            "definition_en": "",
            "definition_zh": "",
            "examples": [],
        }
        # CEFR level — nested inside <span class="def-info"> as
        # <span class="epp-xref dxref B1">B1</span>
        for sp in block.xpath('.//span[contains(@class,"epp-xref")]'):
            t = sp.text_content().strip()
            if re.match(r"^[ABC][12]$", t):
                sense["level"] = t
                break
        # Grammar code — e.g. [T], [I or T], [+ -ing verb]
        # inside <span class="gram dgram"> within def-info
        for sp in block.xpath(
            './/span[contains(@class,"def-info")]//span[contains(@class,"gram")]'
        ):
            sense["grammar"] = sp.text_content().strip()
            break
        # English definition
        def_els = block.xpath(
            './/div[contains(@class,"def") and contains(@class,"ddef_d")]'
        )
        if def_els:
            sense["definition_en"] = _text(def_els[0])
        # Chinese translation
        trans_els = block.xpath(
            './/span[contains(@class,"trans") and contains(@class,"dtrans-se")]'
        )
        if trans_els:
            sense["definition_zh"] = _text(trans_els[0])
        # Usage label
        header_el = block.xpath('.//div[contains(@class,"ddef_h")]')
        if header_el:
            header_text = _text(header_el[0])
            for label in self._USAGE_LABELS:
                if label in header_text.lower():
                    sense["usage"] = label
                    break
        # Examples
        for ex_div in block.xpath(
            './/div[contains(@class,"examp")]'
            '| .//span[contains(@class,"eg")]'
            '[not(parent::div[contains(@class,"examp")])]'
        ):
            en_parts: list[str] = []
            zh_text = ""
            if ex_div.text:
                en_parts.append(ex_div.text.strip())
            for child in ex_div:
                cls = child.get("class", "")
                if "trans" in cls:
                    zh_text = child.text_content().strip()
                else:
                    if child.tag in ("a", "span", "b", "i", "em", "strong"):
                        text = child.text_content()
                        if child.tail:
                            text += child.tail
                        en_parts.append(re.sub(r"\s+", " ", text).strip())
                    elif child.tail:
                        en_parts.append(child.tail.strip())
            en_text = " ".join(p for p in en_parts if p)
            if not en_text:
                continue
            if not zh_text:
                next_span = ex_div.xpath(
                    'following-sibling::span[contains(@class,"trans")][1]'
                )
                if next_span:
                    zh_text = _text(next_span[0])
            if zh_text:
                sense["examples"].append({"en": en_text, "zh": zh_text})
            elif sense.get("phrase"):
                # Phrase entries keep English-only examples
                sense["examples"].append({"en": en_text, "zh": ""})
        return sense

    def _parse_phrase_blocks(self) -> list[dict]:
        """Parse phrase-block divs (phrasal verbs / idioms with inline defs).

        These appear as ``<div class="phrase-block">`` with a
        ``<span class="phrase-title">`` title and a nested
        ``<div class="def-block">`` inside.
        """
        phrases: list[dict] = []
        for pb in self.tree.xpath('//div[contains(@class,"phrase-block")]'):
            sense = {
                "phrase": "",
                "level": "",
                "grammar": "",
                "usage": "",
                "definition_en": "",
                "definition_zh": "",
                "examples": [],
            }
            # Phrase title
            title = pb.xpath('.//span[contains(@class,"phrase-title")]')
            if title:
                sense["phrase"] = _text(title[0])
            # Reuse _parse_def_block on the nested def-block,
            # passing phrase title so English-only examples are kept
            nested = pb.xpath('.//div[contains(@class,"def-block")]')
            if nested:
                db = self._parse_def_block(nested[0], phrase=sense["phrase"])
                sense.update({k: v for k, v in db.items() if k != "phrase"})
            if sense["definition_en"] or sense["definition_zh"]:
                phrases.append(sense)
        # Sort: phrases with zh examples first, English-only last
        phrases.sort(key=lambda s: not any(
            ex.get("zh") for ex in s["examples"]
        ))
        return phrases

    def parse(self) -> dict:
        return {
            "word": self.get_headword(),
            "pos": self.get_part_of_speech(),
            "pronunciation": self.get_pronunciation(),
            "senses": self.get_senses(),
            "url": self.url,
        }

    def is_valid_entry(self) -> bool:
        hw = self.get_headword()
        return bool(hw) and hw not in self._PLACEHOLDER_HW
