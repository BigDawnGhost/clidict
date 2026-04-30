"""CLI entry point — ``camdict <word>``.

camdict hello  → Cambridge English-Chinese dictionary (auto-detected)
camdict пока   → 千亿词霸 Russian-Chinese dictionary (auto-detected)
"""

import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import NoReturn

import requests
from rich.pager import Pager
from rich.text import Text

from camdict.completer import complete as _complete_words
from camdict.config import ENTRY_URL, ENTRY_URL_EN, HEADERS, STYLE_ERROR, STYLE_WORD
from camdict.http import fetch as _raw_fetch
from camdict.parsers.cambridge import CambridgeParser
from camdict.render import console, print_bing_entry, print_entry, print_qianyix_entry


class _LessPager(Pager):
    """less with -F (quit-if-one-screen), -R (colors), -X (no clear on exit)."""

    def show(self, content: str) -> None:  # type: ignore[override]
        env = {**os.environ, "LESSCHARSET": "utf-8"}
        try:
            subprocess.run(["less", "-FRX"], input=content.encode("utf-8"), env=env)
        except FileNotFoundError:
            # Fall back to plain output — Rich export strips ANSI
            # so piping still works on dumb terminals
            sys.stdout.write(content)


def _die(msg: str, completions: str = "") -> NoReturn:
    console.print(f"\n  ❌ {msg}\n", style=STYLE_ERROR)
    if completions:
        _show_completions(completions)
    sys.exit(1)


def _show_completions(prefix: str) -> None:
    """Print completions for *prefix* from the system dictionary.

    When stdout is a tty, uses Rich formatting.  When piped (e.g. fish
    shell tab-completion), outputs plain text, one word per line.
    """
    words = [w for w in _complete_words(prefix) if w != prefix.lower()]
    if not words:
        return
    if not sys.stdout.isatty():
        for w in words:
            sys.stdout.write(w + "\n")
        return
    out = Text("\n  💡 ", style=STYLE_ERROR)
    out.append("你可能想查: ", style=STYLE_ERROR)
    for i, w in enumerate(words):
        if i:
            out.append("  ")
        out.append(w, style=STYLE_WORD)
    console.print(out)


def _is_cyrillic(text: str) -> bool:
    """Return True if *text* contains any Cyrillic character."""
    return any("\u0400" <= ch <= "\u04ff" or "\u0500" <= ch <= "\u052f" for ch in text)


def _print(render_fn, entry: dict) -> None:
    if sys.stdout.isatty():
        with console.pager(styles=True, pager=_LessPager()):
            render_fn(entry)
    else:
        render_fn(entry)


def _lookup_qianyix(word: str) -> None:
    """Look up *word* on 千亿词霸, render and exit."""
    from camdict.parsers.qianyix import QianyixParser

    try:
        parser = QianyixParser.from_url(word)
    except requests.RequestException:
        _die(f"网络请求失败，无法访问千亿词霸: {word}")

    if not parser.is_valid_entry():
        _die(f"千亿词霸中未找到词条: {word}")

    _print(print_qianyix_entry, parser.parse())


def _lookup_cambridge(word: str) -> None:
    """Look up *word* — Cambridge (zh + en) and Bing, 3 parallel requests.

    Priority: Cambridge zh > Cambridge en > Bing.
    Bing result is held back until both Cambridge requests finish.
    """
    from camdict.parsers.bing import BingParser

    cam_result: dict | None = None
    bing_result: dict | None = None

    def _cam_zh():
        nonlocal cam_result
        url = ENTRY_URL.format(word=word.strip().lower())
        resp = _raw_fetch(url, headers=HEADERS)
        p = CambridgeParser(resp.text, url=url)
        if p.is_valid_entry():
            cam_result = p.parse()

    def _cam_en():
        nonlocal cam_result
        url = ENTRY_URL_EN.format(word=word.strip().lower())
        resp = _raw_fetch(url, headers=HEADERS)
        p = CambridgeParser(resp.text, url=url, en_only=True)
        if p.is_valid_entry() and cam_result is None:
            cam_result = p.parse()

    def _bing():
        nonlocal bing_result
        try:
            p = BingParser.from_url(word)
            if p.is_valid_entry():
                bing_result = {
                    "word": p.get_headword(),
                    "pronunciation": p.get_pronunciation(),
                    "inflections": p.get_inflections(),
                    "pos_summary": p.get_pos_summary(),
                }
        except requests.RequestException:
            pass

    with ThreadPoolExecutor(max_workers=3) as ex:
        futures = {
            ex.submit(_cam_zh): "zh",
            ex.submit(_cam_en): "en",
            ex.submit(_bing): "bing",
        }
        for fut in as_completed(futures):
            try:
                fut.result()
            except requests.RequestException:
                pass
            # Cambridge (zh or en) wins immediately
            if cam_result is not None:
                for f in futures:
                    f.cancel()
                _print(print_entry, cam_result)
                return

    # Both Cambridge missed — use Bing if available
    if bing_result is not None:
        _print(print_bing_entry, bing_result)
        return

    _die(f"剑桥词典中未找到词条: {word}", completions=word)


def main() -> None:
    args = sys.argv[1:]

    if not args:
        _die("用法: camdict <单词>  (自动识别英语/俄语)")

    # --_complete PREFIX — hidden flag for shell tab-completion
    if args[0] == "--_complete":
        rest = [a for a in args[1:] if a != "--"]
        if rest:
            for w in _complete_words(rest[0]):
                sys.stdout.write(w + "\n")
        return

    word = args[0]

    if _is_cyrillic(word):
        _lookup_qianyix(word)
    else:
        _lookup_cambridge(word)


if __name__ == "__main__":
    main()
