"""CLI entry point — ``python -m camdict <word>`` or ``camdict -r <word>``.

camdict hello       → Cambridge English-Chinese dictionary
camdict -r пока     → 千亿词霸 Russian-Chinese dictionary
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
        _die("用法: camdict <英文单词>  或  camdict -r <俄文单词>")

    if args[0] == "-r":
        if len(args) < 2:
            _die("用法: camdict -r <俄文单词>")
        _lookup_qianyix(args[1])
        return

    _lookup_cambridge(args[0])


if __name__ == "__main__":
    main()
