"""CLI entry point — ``camdict <word>``.

camdict hello  → Cambridge English-Chinese dictionary (auto-detected)
camdict пока   → 千亿词霸 Russian-Chinese dictionary (auto-detected)
"""

import os
import subprocess
import sys

import requests
from rich.pager import Pager

from camdict.config import STYLE_ERROR
from camdict.parsers.cambridge import CambridgeParser
from camdict.render import console, print_entry, print_qianyix_entry


class _LessPager(Pager):
    """less with -F (quit-if-one-screen), -R (colors), -X (no clear on exit)."""

    @staticmethod
    def show(content: str) -> None:
        env = {**os.environ, "LESSCHARSET": "utf-8"}
        try:
            subprocess.run(["less", "-FRX"], input=content.encode("utf-8"), env=env)
        except FileNotFoundError:
            # Fall back to plain output — Rich export strips ANSI
            # so piping still works on dumb terminals
            sys.stdout.write(content)


def _die(msg: str) -> None:
    console.print(f"\n  ❌ {msg}\n", style=STYLE_ERROR)
    sys.exit(1)


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
    except requests.HTTPError:
        _die(f"网络请求失败，无法访问千亿词霸: {word}")

    if not parser.is_valid_entry():
        _die(f"千亿词霸中未找到词条: {word}")

    _print(print_qianyix_entry, parser.parse())


def _lookup_cambridge(word: str) -> None:
    """Look up *word* on Cambridge Dictionary, render and exit."""
    try:
        parser = CambridgeParser.from_url(word)
    except requests.HTTPError:
        _die(f"网络请求失败，无法访问剑桥词典: {word}")

    if not parser.is_valid_entry():
        _die(f"剑桥词典中未找到词条: {word}")

    _print(print_entry, parser.parse())


def main() -> None:
    args = sys.argv[1:]

    if not args:
        _die("用法: camdict <单词>  (自动识别英语/俄语)")

    word = args[0]

    if _is_cyrillic(word):
        _lookup_qianyix(word)
    else:
        _lookup_cambridge(word)


if __name__ == "__main__":
    main()
