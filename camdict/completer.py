"""Word autocompletion using bundled dictionary files."""

import bisect
from pathlib import Path

_DATA_DIR = Path(__file__).parent / "data"
_DICT_FILES = ("american-english", "british-english")

# ── load ──

_words: list[str] = []


def _load() -> list[str]:
    seen: set[str] = set()
    for name in _DICT_FILES:
        path = _DATA_DIR / name
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            word = line.strip()
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
