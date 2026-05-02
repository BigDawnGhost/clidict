"""CLI entry point — ``clidict <word>``.

clidict hello  → Cambridge English-Chinese dictionary (auto-detected)
clidict пока   → 千亿词霸 Russian-Chinese dictionary (auto-detected)
"""

import logging
import os
import queue
import subprocess
import sys
import threading
from typing import NoReturn

import requests
from rich.pager import Pager
from rich.text import Text

from clidict.completer import complete as _complete_words
from clidict.config import ENTRY_URL, ENTRY_URL_EN, HEADERS, STYLE_ERROR, STYLE_WORD
from clidict.http import fetch as _raw_fetch
from clidict.parsers.cambridge import CambridgeParser
from clidict.render import console, print_bing_entry, print_entry, print_qianyix_entry

logger = logging.getLogger(__name__)


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
    from clidict.parsers.qianyix import QianyixParser

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
    zh always wins; en only used when zh misses.
    """
    from clidict.parsers.bing import BingParser

    word = word.strip().lower()
    cam_zh_result: dict | None = None
    cam_en_result: dict | None = None
    bing_result: dict | None = None

    def _cam_zh():
        nonlocal cam_zh_result
        url = ENTRY_URL.format(word=word)
        resp = _raw_fetch(url, headers=HEADERS)
        p = CambridgeParser(resp.text, url=url)
        if p.is_valid_entry():
            cam_zh_result = p.parse()

    def _cam_en():
        nonlocal cam_en_result
        url = ENTRY_URL_EN.format(word=word)
        resp = _raw_fetch(url, headers=HEADERS)
        p = CambridgeParser(resp.text, url=url, en_only=True)
        if p.is_valid_entry():
            cam_en_result = p.parse()

    def _bing():
        nonlocal bing_result
        p = BingParser.from_url(word)
        if p.is_valid_entry():
            pos = p.get_pos_summary()
            if pos:
                bing_result = {
                    "word": p.get_headword(),
                    "pronunciation": p.get_pronunciation(),
                    "inflections": p.get_inflections(),
                    "pos_summary": pos,
                }

    # Raw daemon threads avoid the ThreadPoolExecutor atexit join delay.
    q: queue.Queue[str] = queue.Queue()

    def _run(name: str, fn) -> None:
        try:
            fn()
        except Exception:
            logger.debug("Request %r failed", name, exc_info=True)
        finally:
            q.put(name)

    for name, fn in (("zh", _cam_zh), ("en", _cam_en), ("bing", _bing)):
        threading.Thread(target=_run, args=(name, fn), daemon=True).start()

    completed: set[str] = set()
    result = None
    render_fn = None
    for _ in range(3):
        completed.add(q.get(timeout=10))
        if cam_zh_result is not None:
            result, render_fn = cam_zh_result, print_entry
            break
        if cam_en_result is not None and "zh" in completed:
            result, render_fn = cam_en_result, print_entry
            break

    if result is not None:
        _print(render_fn, result)
        return

    if bing_result is not None:
        _print(print_bing_entry, bing_result)
        return

    _die(f"剑桥词典中未找到词条: {word}", completions=word)


def main() -> None:
    args = sys.argv[1:]

    if not args:
        _die("用法: clidict <单词>  (自动识别英语/俄语)")

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
