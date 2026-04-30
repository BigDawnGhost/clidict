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

Falls back to the English-only Cambridge dictionary when a word has no bilingual entry.

## Shell completion

**Fish:**

```sh
cp completions/camdict.fish ~/.config/fish/completions/
```

**Bash:**

```sh
echo 'source /path/to/completions/camdict.bash' >> ~/.bashrc
```

Completions are sourced from `/usr/share/dict` (american-english, british-english) and work with both `pip install` and the standalone binary.

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
