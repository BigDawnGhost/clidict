"""CLI entry point — ``camdict <word>``.

camdict hello  → Cambridge English-Chinese dictionary (auto-detected)
camdict пока   → 千亿词霸 Russian-Chinese dictionary (auto-detected)
"""

import os
import subprocess
import sys
from typing import NoReturn

import requests
from rich.pager import Pager
from rich.text import Text

from camdict.completer import complete as _complete_words
from camdict.config import STYLE_ERROR, STYLE_WORD
from camdict.parsers.cambridge import CambridgeParser
from camdict.render import console, print_entry, print_qianyix_entry


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
    """Look up *word* on Cambridge Dictionary, render and exit."""
    try:
        parser = CambridgeParser.from_url(word)
    except requests.RequestException:
        _die(f"网络请求失败，无法访问剑桥词典: {word}")

    if not parser.is_valid_entry():
        _die(f"剑桥词典中未找到词条: {word}", completions=word)

    _print(print_entry, parser.parse())


def main() -> None:
    args = sys.argv[1:]

    if not args:
        _die("用法: camdict <单词>  (自动识别英语/俄语)")

    # --_complete PREFIX — hidden flag for shell tab-completion
    # Works with pip install and PyInstaller binary alike.
    if args[0] == "--_complete":
        # Skip optional "--" separator that some shells insert
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
