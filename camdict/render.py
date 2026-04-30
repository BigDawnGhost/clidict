"""Rich terminal renderer for parsed dictionary entries."""

from rich.console import Console
from rich.table import Table as RichTable
from rich.text import Text

from camdict.config import (
    STYLE_BULLET,
    STYLE_DEF_EN,
    STYLE_DEF_ZH,
    STYLE_EX_EN,
    STYLE_EX_ZH,
    STYLE_FIELD,
    STYLE_GRAMMAR,
    STYLE_INDEX,
    STYLE_IPA,
    STYLE_LEVEL,
    STYLE_PHRASE,
    STYLE_POS,
    STYLE_RU_DEF,
    STYLE_RU_EX_RU,
    STYLE_RU_EX_ZH,
    STYLE_RU_WORD,
    STYLE_SECTION,
    STYLE_STRESS,
    STYLE_TABLE_HDR,
    STYLE_TABLE_ROW,
    STYLE_UK,
    STYLE_US,
    STYLE_USAGE,
    STYLE_WORD,
)

console = Console()


# ═══════════════════════════════════════════════════════════════════
#  Cambridge Dictionary (English-Chinese)
# ═══════════════════════════════════════════════════════════════════


def _render_entry(entry: dict) -> Text:
    out = Text()
    out.append(entry["word"], style=STYLE_WORD)
    if entry.get("pos"):
        out.append(f"  {entry['pos']}", style=STYLE_POS)
    pron = entry.get("pronunciation", {})
    if pron.get("UK") or pron.get("US"):
        out.append("\n")
        if pron.get("UK"):
            out.append("UK ", style=STYLE_UK)
            out.append(pron["UK"], style=STYLE_IPA)
        if pron.get("US"):
            if pron.get("UK"):
                out.append("  ")
            out.append("US ", style=STYLE_US)
            out.append(pron["US"], style=STYLE_IPA)
    reg_i = 0
    phr_i = 0
    for sense in entry.get("senses", []):
        phrase = sense.get("phrase", "")
        if phrase:
            # First phrase — print section header
            if phr_i == 0:
                out.append("\n\n短语", style=STYLE_SECTION)
            phr_i += 1
            out.append(f"\n{phr_i}. ", style=STYLE_INDEX)
            out.append(phrase, style=STYLE_PHRASE)
            if sense.get("level"):
                out.append(f" [{sense['level']}]", style=STYLE_LEVEL)
            if sense.get("grammar"):
                out.append(f" {sense['grammar']}", style=STYLE_GRAMMAR)
            if sense.get("usage"):
                if sense.get("level") or sense.get("grammar"):
                    out.append(" ")
                out.append(f"[{sense['usage']}]", style=STYLE_USAGE)
            out.append("\n    ")
            if sense.get("definition_en"):
                out.append(sense["definition_en"], style=STYLE_DEF_EN)
            # For phrases, definition_zh is usually the example's
            # translation — skip it when examples are present
            if sense.get("definition_zh") and not sense.get("examples"):
                if sense.get("definition_en"):
                    out.append("\n    ")
                out.append(sense["definition_zh"], style=STYLE_DEF_ZH)
        else:
            reg_i += 1
            out.append(f"\n{reg_i}. ", style=STYLE_INDEX)
            if sense.get("level"):
                out.append(f"[{sense['level']}]", style=STYLE_LEVEL)
            if sense.get("grammar"):
                if sense.get("level"):
                    out.append(" ")
                out.append(sense["grammar"], style=STYLE_GRAMMAR)
            if sense.get("usage"):
                if sense.get("level") or sense.get("grammar"):
                    out.append(" ")
                out.append(f"[{sense['usage']}]", style=STYLE_USAGE)
            if sense.get("level") or sense.get("grammar") or sense.get("usage"):
                out.append("\n    ")
            if sense.get("definition_en"):
                out.append(sense["definition_en"], style=STYLE_DEF_EN)
            if sense.get("definition_zh"):
                out.append("\n    ")
                out.append(sense["definition_zh"], style=STYLE_DEF_ZH)
        for ex in sense.get("examples", []):
            out.append("\n    \u2022 ", style=STYLE_BULLET)
            out.append(ex.get("en", ""), style=STYLE_EX_EN)
            if ex.get("zh"):
                out.append("\n      ", style=STYLE_BULLET)
                out.append(ex["zh"], style=STYLE_EX_ZH)
    return out


def print_entry(entry: dict) -> None:
    console.print(_render_entry(entry))


# ═══════════════════════════════════════════════════════════════════
#  千亿词霸 (Russian-Chinese)
# ═══════════════════════════════════════════════════════════════════


def _stress_text(word: str) -> Text:
    """Render a Russian word with the stressed vowel highlighted in red.

    Stress is U+0301 (combining acute) placed after the vowel.
    """
    out = Text()
    i = 0
    while i < len(word):
        ch = word[i]
        if i + 1 < len(word) and word[i + 1] == "\u0301":
            out.append(ch, style=STYLE_STRESS)
            i += 2
        else:
            out.append(ch, style=STYLE_RU_WORD)
            i += 1
    return out


def _build_conj_table(label: str, rows: list[list[str]]) -> RichTable:
    """Build a Rich Table for a conjugation / declension grid."""
    if not rows:
        return RichTable()

    ncols = max(len(r) for r in rows)
    has_row_headers = bool(rows[0]) and rows[0][0] == ""

    tbl = RichTable(
        title=label,
        title_style=STYLE_SECTION,
        title_justify="center",
        header_style=STYLE_TABLE_HDR,
        border_style="bright_black",
        show_lines=True,
        expand=False,
    )

    if has_row_headers:
        tbl.add_column("", style=STYLE_TABLE_HDR, no_wrap=True)
        col_start = 1
        headers = rows[0]
        data_rows = rows[1:]
    else:
        col_start = 0
        headers = rows[0]
        data_rows = rows[1:]

    for c in range(col_start, ncols):
        hdr = headers[c] if c < len(headers) else ""
        tbl.add_column(hdr, style=STYLE_TABLE_HDR, no_wrap=True)

    for row in data_rows:
        rendered = []
        for c in range(ncols):
            val = row[c] if c < len(row) else ""
            if c == 0 and has_row_headers:
                rendered.append(Text(val, style=STYLE_TABLE_HDR))
            else:
                rendered.append(
                    _stress_text(val) if val else Text("/", style=STYLE_TABLE_ROW)
                )
        tbl.add_row(*rendered)

    return tbl


def print_qianyix_entry(entry: dict) -> None:
    """Render a Qianyix entry with stress-marked headword and all
    conjugation / declension tables."""

    bases = entry.get("bases", [])
    multiple = len(bases) > 1

    console.print(_stress_text(entry.get("word", "")))

    for i, base in enumerate(bases):
        if i > 0:
            console.print()

        if multiple and base["word"] and base["word"] != entry["word"]:
            console.print(_stress_text(base["word"]))

        if base["definitions"]:
            defs = " \u00b7 ".join(base["definitions"])
            console.print(Text(defs, style=STYLE_RU_DEF))

        if base["industries"]:
            console.print()
            console.print(Text("行业释义", style=STYLE_SECTION))
            for item in base["industries"]:
                console.print(
                    Text("  ")
                    + Text(item["field"], style=STYLE_FIELD)
                    + Text("  ")
                    + Text(item["zh"], style=STYLE_RU_DEF)
                )

        if base["examples"]:
            console.print()
            console.print(Text("例句", style=STYLE_SECTION))
            for j, ex in enumerate(base["examples"], 1):
                console.print(
                    Text(f"  {j}. ", style=STYLE_INDEX)
                    + Text(ex["zh"], style=STYLE_RU_EX_ZH)
                )
                console.print(Text("     ") + Text(ex["ru"], style=STYLE_RU_EX_RU))

        if base["conjugations"]:
            console.print()
            console.print(Text("变位变格", style=STYLE_SECTION))
            for tbl in base["conjugations"]:
                rich_tbl = _build_conj_table(tbl["label"], tbl["rows"])
                console.print(rich_tbl)
