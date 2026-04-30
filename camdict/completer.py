"""Word autocompletion using system dictionaries from /usr/share/dict."""

import bisect
from pathlib import Path

DICT_DIR = Path("/usr/share/dict")
DICT_FILES = ("american-english", "british-english")

# ── load ──

_words: list[str] = []


def _load() -> list[str]:
    """Load, merge, deduplicate, and filter system word lists.

    Returns a sorted list of lowercase-only words (≥ 3 chars),
    excluding possessives (``'s``) and single-letter entries.
    """
    seen: set[str] = set()
    for name in DICT_FILES:
        path = DICT_DIR / name
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            word = line.strip()
            # Keep only all-lowercase common words, ≥ 3 chars,
            # no possessives / contractions
            if len(word) >= 3 and word.islower() and word.isascii() and "'" not in word:
                seen.add(word)
    return sorted(seen)


def _ensure_loaded() -> None:
    global _words
    if not _words:
        _words = _load()


# ── public API ──


def complete(prefix: str, limit: int = 20) -> list[str]:
    """Return words starting with *prefix* (case-insensitive)."""
    _ensure_loaded()
    p = prefix.lower()
    lo = bisect.bisect_left(_words, p)
    hi = lo
    while hi < len(_words) and _words[hi].startswith(p):
        hi += 1
        if hi - lo >= limit:
            break
    return _words[lo:hi]


if __name__ == "__main__":
    import sys

    prefix = sys.argv[1] if len(sys.argv) > 1 else ""
    for w in complete(prefix):
        print(w)
