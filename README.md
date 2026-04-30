# camdict

Terminal dictionary lookup. Automatically routes by language:

- **English** → [Cambridge Dictionary](https://dictionary.cambridge.org) (英汉双语)
- **Russian** → [千亿词霸](https://w.qianyix.com) (俄汉双语)

Detection is character-based: any Cyrillic input goes to 千亿词霸, everything else to Cambridge.

## Install

```sh
uv tool install git+https://github.com/BigDawnGhost/camdict
# or
pip install .
```

## Usage

```sh
camdict hello
camdict phrasal verb
camdict привет
```

Cambridge entries show CEFR level, grammar codes, UK/US pronunciation, Chinese translations, and example sentences. Russian entries include stress marks, industry meanings, and conjugation/declension tables.

### Lookup flow

3 HTTP requests fire in parallel: Cambridge (zh), Cambridge (en), and Bing. Priority order:

1. Cambridge Chinese-English (fastest path)
2. Cambridge English-only
3. [Bing Dictionary](https://cn.bing.com/dict) (fallback)

When Cambridge misses a word (e.g. `genshin`), Bing takes over automatically.

## Shell completion

**Fish:**

```sh
cp completions/camdict.fish ~/.config/fish/completions/
```

**Bash:**

```sh
echo 'source /path/to/completions/camdict.bash' >> ~/.bashrc
```

Completions are sourced from bundled word lists (american-english + british-english) and work with both `pip install` and the standalone binary.

## Build standalone binary

Requires [PyInstaller](https://pyinstaller.org):

```sh
uv run pyinstaller camdict.spec
# binary at dist/camdict
```

## Development

```sh
uv sync
uv run pytest
```
