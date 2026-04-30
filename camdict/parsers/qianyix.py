"""千亿词霸 (qianyix.com) Russian-Chinese dictionary parser.

Focus: stress marks (重音), conjugation/declension tables (变位变格),
       and short definitions. Examples limited to first few.

DOM structure (each entry = base div + following sibling panels):
    div#base0.panel.panel-default.baseword
    ├── .panel-heading ...
    └── .panel-body.view
        ├── h2.keyword  (word with <b> stress marks)
        └── p.exp       (short definitions)
    div#detail0.panel.panel-default.subs     ← industry meanings
    div#example0.panel.panel-default.example  ← example sentences
    div#grm0.panel.panel-default              ← conjugation tables
    div#base1  ... (next entry)
"""

import re
from urllib.parse import quote

from lxml import html

from camdict.config import USER_AGENT
from camdict.http import fetch

BASE_URL = "https://w.qianyix.com/index.php"
SEARCH_URL = BASE_URL + "?q={word}"

HEADERS = {"User-Agent": USER_AGENT}


def _text(el) -> str:
    """Get cleaned, whitespace-normalised text of an element."""
    if el is None:
        return ""
    return re.sub(r"\s+", " ", el.text_content()).strip()


def _extract_stress(el) -> str:
    """Extract word with stress marker from <b> tags.

    Example: показ<b>а</b>ть → пока́зать (U+0301 combining acute)
    """
    parts = []
    if el.text:
        parts.append(el.text)
    for child in el:
        if child.tag == "b":
            vowel = child.text or ""
            parts.append(vowel + "\u0301")
            if child.tail:
                parts.append(child.tail)
        else:
            parts.append(child.text_content() or "")
            if child.tail:
                parts.append(child.tail)
    return re.sub(r"\s+", " ", "".join(parts)).strip()


class QianyixParser:
    """Parse a 千亿词霸 Russian-Chinese dictionary page."""

    MAX_EXAMPLES = 5

    def __init__(self, html_content: bytes | str, word: str = ""):
        self.tree = html.fromstring(html_content)
        self.word = word

    @classmethod
    def from_url(cls, word: str, timeout: int = 10) -> "QianyixParser":
        url = SEARCH_URL.format(word=quote(word.strip()))
        resp = fetch(url, headers=HEADERS, timeout=timeout)
        return cls(resp.content, word=word.strip())

    # ── top-level extraction ─────────────────────────────────────

    def get_headword(self) -> str:
        """Return the primary headword (with stress marks)."""
        kw = self.tree.xpath('//h2[contains(@class,"keyword")][1]')
        if kw:
            return _extract_stress(kw[0])
        return self.word

    def get_bases(self) -> list[dict]:
        """Return all word-entry blocks on the page.

        Each entry = a base div (id=baseN) plus its associated
        detail / example / conjugation sibling panels.
        Uses ``getnext()`` so entries at different DOM depths
        (e.g. base0 inside .col-md-7, base1 directly under <html>)
        are handled identically.
        """
        results: list[dict] = []
        base_divs = self.tree.xpath(
            '//div[starts-with(@id,"base") and not(contains(@id,"-"))]'
        )

        for base_el in base_divs:
            block = self._parse_one_entry(base_el)
            if block["definitions"] or block["conjugations"]:
                results.append(block)

        return results

    def _parse_one_entry(self, base_el) -> dict:
        """Parse a single entry starting from its base div."""
        block: dict = {
            "word": "",
            "definitions": [],
            "examples": [],
            "conjugations": [],
            "industries": [],
        }

        # 1. Extract keyword & definitions from inside the base div
        kw = base_el.xpath('.//h2[contains(@class,"keyword")]')
        if kw:
            block["word"] = _extract_stress(kw[0])

        exp = base_el.xpath('.//p[@class="exp"]')
        if exp:
            lines = [t.strip() for t in exp[0].itertext() if t.strip()]
            if not lines:
                lines = [
                    ln.strip() for ln in exp[0].text_content().split("\n") if ln.strip()
                ]
            block["definitions"] = lines

        # 2. Walk following siblings collecting associated panels
        nxt = base_el.getnext()
        while nxt is not None:
            tag = nxt.tag if isinstance(nxt.tag, str) else ""
            if tag != "div":
                nxt = nxt.getnext()
                continue

            nid = nxt.get("id", "")
            cls = nxt.get("class", "")

            # Stop when we hit another base div
            if nid.startswith("base") and "-" not in nid:
                break

            if "subs" in cls:
                block["industries"] = self._parse_industries(nxt)
            elif "example" in cls:
                block["examples"] = self._parse_examples(nxt)
            elif "panel" in cls:
                # Conjugation / declension panel (has "变位变格" in heading)
                heading = nxt.xpath('.//*[contains(text(),"变位变格")]')
                if heading:
                    block["conjugations"] = self._parse_conjugation(nxt)

            nxt = nxt.getnext()

        return block

    # ── sub-parsers ───────────────────────────────────────────────

    def _parse_industries(self, div_el) -> list[dict]:
        """Parse industry-specific meanings from a subs panel."""
        items: list[dict] = []
        for row in div_el.xpath('.//div[contains(@class,"row")]'):
            cells = row.xpath("./div")
            if len(cells) >= 2:
                field = _text(cells[0])
                zh = _text(cells[1])
                if field and zh:
                    items.append({"field": field, "zh": zh})
        return items

    def _parse_examples(self, div_el) -> list[dict]:
        """Parse example sentences.

        <p> elements come in pairs: Chinese first, then Russian.
        """
        items: list[dict] = []
        ps = div_el.xpath(".//p")
        texts = []
        for p_el in ps:
            t = _text(p_el)
            if t and not re.match(r"^\d+\.?$", t):
                texts.append(t)

        for i in range(0, min(len(texts) - 1, self.MAX_EXAMPLES * 2), 2):
            items.append({"zh": texts[i], "ru": texts[i + 1]})
        return items

    def _parse_conjugation(self, div_el) -> list[dict]:
        """Parse conjugation / declension tables.

        The h2/h3/table elements live inside .panel-body (or .grammardiv),
        not as direct children of the grm div.

        Structure:
            <h2>主动语态</h2>
            <h3>现在/将来时</h3>
            <table> ... </table>
            <h3>过去时</h3>
            <table> ... </table>
            ...
            <h2>被动语态</h2>
            <h3>过去时形动词</h3>
            <table> ... </table>

        Each table's label combines the nearest h2 + h3 context.
        """
        # Drill into .panel-body > .grammardiv (or just .panel-body)
        container = div_el
        for cls in ("panel-body", "grammardiv"):
            cand = container.xpath(f'.//*[contains(@class,"{cls}")]')
            if cand:
                container = cand[0]

        tables: list[dict] = []
        current_h2 = ""

        for child in container:
            if not isinstance(child.tag, str):
                continue

            if child.tag == "h2":
                current_h2 = _text(child)
            elif child.tag == "h3":
                h3_label = _text(child)
                tbl = self._find_next_table(child)
                if tbl is not None:
                    label = f"{current_h2} · {h3_label}" if current_h2 else h3_label
                    rows = self._extract_table_rows(tbl)
                    if rows:
                        tables.append({"label": label, "rows": rows})
            elif child.tag == "table" and not self._has_preceding_h3(child):
                # Standalone table (no h3 label immediately before it)
                rows = self._extract_table_rows(child)
                if rows:
                    label = current_h2 or ""
                    tables.append({"label": label, "rows": rows})

        return tables

    @staticmethod
    def _has_preceding_h3(table_el) -> bool:
        """True if *table_el* has an <h3> among its preceding siblings
        (skipping whitespace-only text nodes)."""
        prev = table_el.getprevious()
        while prev is not None:
            if isinstance(prev.tag, str):
                return prev.tag == "h3"
            # Skip non-element nodes (e.g. tail text)
            prev = prev.getprevious()
        return False

    @staticmethod
    def _find_next_table(after_el):
        """Find the first <table> among following siblings of *after_el*."""
        nxt = after_el.getnext()
        while nxt is not None:
            if isinstance(nxt.tag, str) and nxt.tag == "table":
                return nxt
            nxt = nxt.getnext()
        return None

    @staticmethod
    def _extract_table_rows(table_el) -> list[list[str]]:
        """Extract 2-D list of cell texts from a <table>."""
        rows = []
        for tr in table_el.xpath(".//tr"):
            row = []
            for cell in tr.xpath("./th | ./td"):
                row.append(_extract_stress(cell))
            if row:
                rows.append(row)
        return rows

    # ── entry point ──────────────────────────────────────────────

    def parse(self) -> dict:
        return {
            "word": self.get_headword(),
            "bases": self.get_bases(),
        }

    def is_valid_entry(self) -> bool:
        return bool(self.tree.xpath('//h2[contains(@class,"keyword")]'))
