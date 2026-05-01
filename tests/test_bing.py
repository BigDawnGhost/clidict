"""Robustness tests for clidict.parsers.bing.BingParser."""

from lxml import html as lxml_html

from clidict.parsers.bing import BingParser, _parse_pron, _text

# ── _text helper ──────────────────────────────────────────────────────────


def _el(html_str: str):
    return lxml_html.fromstring(html_str)


def test_text_none_returns_default():
    assert _text(None) == ""


def test_text_none_custom_default():
    assert _text(None, default="x") == "x"


def test_text_collapses_whitespace():
    el = _el("<p>  hello   world  </p>")
    assert _text(el) == "hello world"


def test_text_nested():
    el = _el("<div>foo <b>bar</b> baz</div>")
    assert _text(el) == "foo bar baz"


def test_text_empty():
    el = _el("<p></p>")
    assert _text(el) == ""


# ── _parse_pron ───────────────────────────────────────────────────────────


def test_parse_pron_standard():
    assert _parse_pron("US [ˈæp.əl]") == "ˈæp.əl"


def test_parse_pron_no_brackets():
    assert _parse_pron("no pronunciation") == ""


def test_parse_pron_multiple_brackets():
    assert _parse_pron("[UK] [ˈtest]") == "UK"


# ── is_valid_entry ────────────────────────────────────────────────────────

VALID_HTML = """<html><body>
  <div class="hd_div"><strong>apple</strong></div>
</body></html>"""

NO_ENTRY_HTML = """<html><body>
  <p>No results found.</p>
</body></html>"""


def test_is_valid_entry_true():
    assert BingParser(VALID_HTML, "apple").is_valid_entry() is True


def test_is_valid_entry_false():
    assert BingParser(NO_ENTRY_HTML).is_valid_entry() is False


def test_is_valid_entry_empty_html():
    assert BingParser("<html><body></body></html>").is_valid_entry() is False


# ── get_headword ──────────────────────────────────────────────────────────


def test_get_headword_from_hd_div():
    hw = BingParser(VALID_HTML, "apple").get_headword()
    assert hw == "apple"


def test_get_headword_fallback_to_word():
    hw = BingParser(NO_ENTRY_HTML, "genshin").get_headword()
    assert hw == "genshin"


def test_get_headword_whitespace_normalized():
    html = """<html><body>
      <div class="hd_div"><strong>  run  out  </strong></div>
    </body></html>"""
    assert BingParser(html).get_headword() == "run out"


# ── get_pronunciation ─────────────────────────────────────────────────────

PRON_BOTH = """<html><body>
  <div class="hd_div"><strong>test</strong></div>
  <div class="hd_prUS">US [ˈtɛst]</div>
  <div class="hd_pr">UK [tɛst]</div>
</body></html>"""


def test_pronunciation_both_regions():
    pron = BingParser(PRON_BOTH).get_pronunciation()
    assert pron["UK"] == "tɛst"
    assert pron["US"] == "ˈtɛst"


def test_pronunciation_us_only():
    html = """<html><body>
      <div class="hd_div"><strong>x</strong></div>
      <div class="hd_prUS">US [ɛks]</div>
    </body></html>"""
    pron = BingParser(html).get_pronunciation()
    assert pron["US"] == "ɛks"
    assert pron["UK"] == ""


def test_pronunciation_missing():
    pron = BingParser(NO_ENTRY_HTML).get_pronunciation()
    assert pron == {"UK": "", "US": ""}


# ── get_inflections ───────────────────────────────────────────────────────

INFL_HTML = """<html><body>
  <div class="hd_div"><strong>run</strong></div>
  <div class="hd_if">runs, running, ran, run</div>
</body></html>"""


def test_get_inflections():
    assert BingParser(INFL_HTML).get_inflections() == "runs, running, ran, run"


def test_get_inflections_missing():
    assert BingParser(NO_ENTRY_HTML).get_inflections() == ""


# ── get_pos_summary ───────────────────────────────────────────────────────

POS_FULL = """<html><body>
  <div class="hd_div"><strong>apple</strong></div>
  <ul>
    <li><span class="pos">n.</span><span class="def">苹果</span></li>
    <li><span class="pos">adj.</span><span class="def">苹果的</span></li>
  </ul>
</body></html>"""


def test_pos_summary_multiple():
    items = BingParser(POS_FULL).get_pos_summary()
    assert len(items) == 2
    assert items[0] == {"pos": "n.", "zh": "苹果"}
    assert items[1] == {"pos": "adj.", "zh": "苹果的"}


def test_pos_summary_empty():
    assert BingParser(NO_ENTRY_HTML).get_pos_summary() == []


def test_pos_summary_missing_pos_span():
    html = """<html><body>
      <ul><li><span class="def">只有中文</span></li></ul>
    </body></html>"""
    # li without span.pos → skipped by xpath filter
    assert BingParser(html).get_pos_summary() == []


# ── parse() contract ──────────────────────────────────────────────────────


def test_parse_keys():
    result = BingParser(VALID_HTML, "apple").parse()
    assert set(result.keys()) == {"word", "pronunciation", "inflections", "pos_summary"}


def test_parse_word():
    result = BingParser(VALID_HTML, "apple").parse()
    assert result["word"] == "apple"


def test_parse_full_entry():
    html = """<html><body>
      <div class="hd_div"><strong>run</strong></div>
      <div class="hd_prUS">US [rʌn]</div>
      <div class="hd_pr">UK [rʌn]</div>
      <div class="hd_if">runs, running, ran</div>
      <ul>
        <li><span class="pos">v.</span><span class="def">跑</span></li>
      </ul>
    </body></html>"""
    result = BingParser(html, "run").parse()
    assert result["word"] == "run"
    assert result["pronunciation"]["UK"] == "rʌn"
    assert result["pronunciation"]["US"] == "rʌn"
    assert result["inflections"] == "runs, running, ran"
    assert len(result["pos_summary"]) == 1


# ── Edge cases ────────────────────────────────────────────────────────────


def test_minimal_html_no_crash():
    p = BingParser("<html><body></body></html>")
    assert p.get_headword() == ""
    assert p.get_pronunciation() == {"UK": "", "US": ""}
    assert p.get_inflections() == ""
    assert p.get_pos_summary() == []
    assert p.is_valid_entry() is False


def test_empty_strong_tag():
    html = """<html><body>
      <div class="hd_div"><strong>   </strong></div>
    </body></html>"""
    assert BingParser(html).get_headword() == ""


def test_pronunciation_no_bracket_content():
    # hd_pr div with text that has no [...] part
    html = """<html><body>
      <div class="hd_div"><strong>x</strong></div>
      <div class="hd_pr">bad format</div>
    </body></html>"""
    pron = BingParser(html).get_pronunciation()
    assert pron["UK"] == ""


def test_pos_summary_skips_non_pos_li():
    html = """<html><body>
      <div class="hd_div"><strong>x</strong></div>
      <ul>
        <li>no spans here</li>
        <li><span class="pos">n.</span><span class="def">定义</span></li>
      </ul>
    </body></html>"""
    items = BingParser(html).get_pos_summary()
    assert len(items) == 1
