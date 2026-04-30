"""Robustness tests for camdict.parsers.cambridge.CambridgeParser."""

from lxml import html as lxml_html

from camdict.parsers.cambridge import CambridgeParser, _text

# ── _text helper ──────────────────────────────────────────────────────────


def test_text_none_returns_default():
    assert _text(None) == ""


def test_text_none_custom_default():
    assert _text(None, default="x") == "x"


def test_text_collapses_whitespace():
    el = lxml_html.fromstring("<p>  hello   world  </p>")
    assert _text(el) == "hello world"


def test_text_nested_elements():
    el = lxml_html.fromstring("<div>foo <b>bar</b> baz</div>")
    assert _text(el) == "foo bar baz"


def test_text_empty_element():
    el = lxml_html.fromstring("<p></p>")
    assert _text(el) == ""


# ── get_headword ──────────────────────────────────────────────────────────

HW_SPAN = """<html><body>
  <span class="headword hdb dhw">apple</span>
</body></html>"""

HW_META = """<html>
  <head><meta property="og:title" content="apple - Cambridge Dictionary"/></head>
  <body></body>
</html>"""

HW_NONE = "<html><body><p>nothing here</p></body></html>"


def test_headword_from_span():
    assert CambridgeParser(HW_SPAN).get_headword() == "apple"


def test_headword_fallback_to_meta():
    assert CambridgeParser(HW_META).get_headword() == "apple - Cambridge Dictionary"


def test_headword_empty_when_missing():
    assert CambridgeParser(HW_NONE).get_headword() == ""


def test_headword_whitespace_normalized():
    html = '<html><body><span class="headword">  run  out  </span></body></html>'
    assert CambridgeParser(html).get_headword() == "run out"


# ── is_valid_entry ────────────────────────────────────────────────────────


def test_valid_entry_true():
    assert CambridgeParser(HW_SPAN).is_valid_entry() is True


def test_valid_entry_false_when_no_headword():
    assert CambridgeParser(HW_NONE).is_valid_entry() is False


def test_valid_entry_false_for_placeholder():
    html = '<html><body><span class="headword">剑桥词典：英语-中文(简体)翻译</span></body></html>'
    assert CambridgeParser(html).is_valid_entry() is False


def test_valid_entry_false_for_empty_headword():
    html = '<html><body><span class="headword">   </span></body></html>'
    assert CambridgeParser(html).is_valid_entry() is False


# ── get_part_of_speech ────────────────────────────────────────────────────

POS_HTML = """<html><body>
  <div class="pos-header">
    <span class="pos dpos">noun</span>
    <span class="pos dpos">verb</span>
    <span class="pos dpos">noun</span>
    <span class="pos dpos">FAKEPOS</span>
  </div>
</body></html>"""


def test_pos_dedup_and_filter():
    assert CambridgeParser(POS_HTML).get_part_of_speech() == "noun, verb"


def test_pos_empty_when_missing():
    assert CambridgeParser(HW_NONE).get_part_of_speech() == ""


def test_pos_case_insensitive():
    html = """<html><body><div class="pos-header">
      <span class="pos dpos">Noun</span>
    </div></body></html>"""
    assert CambridgeParser(html).get_part_of_speech() == "noun"


# ── get_pronunciation ─────────────────────────────────────────────────────

PRON_BOTH = """<html><body>
  <span class="uk dpron-i"><span class="pron dpron">/ˈæp.əl/</span></span>
  <span class="us dpron-i"><span class="pron dpron">/ˈæp.əl/</span></span>
</body></html>"""


def test_pronunciation_both_regions():
    pron = CambridgeParser(PRON_BOTH).get_pronunciation()
    assert pron["UK"] == "/ˈæp.əl/"
    assert pron["US"] == "/ˈæp.əl/"


def test_pronunciation_uk_only():
    html = """<html><body>
      <span class="uk dpron-i"><span class="pron dpron">/test/</span></span>
    </body></html>"""
    pron = CambridgeParser(html).get_pronunciation()
    assert pron["UK"] == "/test/"
    assert pron["US"] == ""


def test_pronunciation_missing():
    pron = CambridgeParser(HW_NONE).get_pronunciation()
    assert pron == {"UK": "", "US": ""}


def test_pronunciation_empty_pron_span():
    html = """<html><body>
      <span class="uk dpron-i"><span class="pron dpron">  </span></span>
    </body></html>"""
    pron = CambridgeParser(html).get_pronunciation()
    assert pron["UK"] == ""


# ── _parse_def_block / get_senses ─────────────────────────────────────────

DEF_FULL = """<html><body>
<div class="def-block ddef_block">
  <div class="ddef_h">
    <span class="def-info ddef-info">
      <span class="epp-xref dxref B1">B1</span>
    </span>
    informal
  </div>
  <div class="def ddef_d db">a round fruit</div>
  <span class="trans dtrans dtrans-se">苹果</span>
  <div class="examp dexamp">I ate an apple.
    <span class="trans dtrans">我吃了一个苹果。</span>
  </div>
</div>
</body></html>"""


def test_full_def_block():
    senses = CambridgeParser(DEF_FULL).get_senses()
    assert len(senses) == 1
    s = senses[0]
    assert s["level"] == "B1"
    assert s["usage"] == "informal"
    assert "round fruit" in s["definition_en"]
    assert s["definition_zh"] == "苹果"
    assert len(s["examples"]) == 1
    assert s["examples"][0]["en"] == "I ate an apple."
    assert s["examples"][0]["zh"] == "我吃了一个苹果。"


def test_def_block_no_examples():
    html = """<html><body>
    <div class="def-block ddef_block">
      <div class="def ddef_d db">a type of fruit</div>
      <span class="trans dtrans dtrans-se">水果</span>
    </div></body></html>"""
    senses = CambridgeParser(html).get_senses()
    assert senses[0]["examples"] == []


def test_def_block_only_zh_kept():
    html = """<html><body>
    <div class="def-block ddef_block">
      <span class="trans dtrans dtrans-se">仅有中文</span>
    </div></body></html>"""
    senses = CambridgeParser(html).get_senses()
    assert len(senses) == 1
    assert senses[0]["definition_en"] == ""
    assert senses[0]["definition_zh"] == "仅有中文"


def test_def_block_empty_filtered():
    html = """<html><body>
    <div class="def-block ddef_block"></div>
    </body></html>"""
    assert CambridgeParser(html).get_senses() == []


def test_cefr_levels_parsed():
    for level in ("A1", "A2", "B1", "B2", "C1", "C2"):
        html = f"""<html><body>
        <div class="def-block ddef_block">
          <span class="def-info ddef-info">
            <span class="epp-xref dxref {level}">{level}</span>
          </span>
          <div class="def ddef_d db">definition</div>
          <span class="trans dtrans dtrans-se">释义</span>
        </div></body></html>"""
        s = CambridgeParser(html).get_senses()[0]
        assert s["level"] == level, f"Failed for {level}"


def test_invalid_cefr_ignored():
    html = """<html><body>
    <div class="def-block ddef_block">
      <span class="def-info ddef-info">X9</span>
      <div class="def ddef_d db">definition</div>
      <span class="trans dtrans dtrans-se">释义</span>
    </div></body></html>"""
    assert CambridgeParser(html).get_senses()[0]["level"] == ""


def test_grammar_code_extracted():
    html = """<html><body>
    <div class="def-block ddef_block">
      <span class="def-info ddef-info">
        <span class="gram dgram">[I or T]</span>
      </span>
      <div class="def ddef_d db">to move</div>
      <span class="trans dtrans dtrans-se">移动</span>
    </div></body></html>"""
    assert CambridgeParser(html).get_senses()[0]["grammar"] == "[I or T]"


def test_multiple_senses():
    html = """<html><body>
    <div class="def-block ddef_block">
      <div class="def ddef_d db">sense one</div>
      <span class="trans dtrans dtrans-se">义一</span>
    </div>
    <div class="def-block ddef_block">
      <div class="def ddef_d db">sense two</div>
      <span class="trans dtrans dtrans-se">义二</span>
    </div>
    </body></html>"""
    senses = CambridgeParser(html).get_senses()
    assert len(senses) == 2
    assert senses[0]["definition_zh"] == "义一"
    assert senses[1]["definition_zh"] == "义二"


# ── Example sentence edge cases ───────────────────────────────────────────


def test_example_sibling_translation():
    html = """<html><body>
    <div class="def-block ddef_block">
      <div class="def ddef_d db">def</div>
      <span class="trans dtrans dtrans-se">释义</span>
      <div class="examp dexamp">She ran quickly.</div>
      <span class="trans dtrans dtrans-se hdb break-cj">她跑得很快。</span>
    </div></body></html>"""
    ex = CambridgeParser(html).get_senses()[0]["examples"][0]
    assert ex["en"] == "She ran quickly."
    assert ex["zh"] == "她跑得很快。"


def test_example_without_translation_kept():
    html = """<html><body>
    <div class="def-block ddef_block">
      <div class="def ddef_d db">a word</div>
      <span class="trans dtrans dtrans-se">一个词</span>
      <div class="examp dexamp">No translation here.</div>
    </div></body></html>"""
    assert CambridgeParser(html).get_senses()[0]["examples"] == [{"en": "No translation here.", "zh": ""}]


def test_example_inline_styled_no_spurious_space():
    html = """<html><body>
    <div class="def-block ddef_block">
      <div class="def ddef_d db">def</div>
      <span class="trans dtrans dtrans-se">释义</span>
      <div class="examp dexamp"><b>Bold</b>, then normal.
        <span class="trans dtrans">粗体，然后普通。</span>
      </div>
    </div></body></html>"""
    ex = CambridgeParser(html).get_senses()[0]["examples"][0]
    assert "Bold," in ex["en"]  # no space before comma
    assert "then normal." in ex["en"]


def test_example_trans_tail_not_in_english():
    # trans span with tail text — tail must NOT appear in en_text
    html = """<html><body>
    <div class="def-block ddef_block">
      <div class="def ddef_d db">def</div>
      <span class="trans dtrans dtrans-se">释义</span>
      <div class="examp dexamp">English sentence.
        <span class="trans dtrans">中文翻译。</span>SHOULD_NOT_APPEAR
      </div>
    </div></body></html>"""
    ex = CambridgeParser(html).get_senses()[0]["examples"][0]
    assert "SHOULD_NOT_APPEAR" not in ex["en"]
    assert ex["zh"] == "中文翻译。"


def test_example_empty_en_text_excluded():
    html = """<html><body>
    <div class="def-block ddef_block">
      <div class="def ddef_d db">def</div>
      <span class="trans dtrans dtrans-se">释义</span>
      <div class="examp dexamp">
        <span class="trans dtrans">只有中文，没有英文。</span>
      </div>
    </div></body></html>"""
    # en_text would be empty → example excluded
    assert CambridgeParser(html).get_senses()[0]["examples"] == []


# ── parse() output contract ───────────────────────────────────────────────


def test_parse_keys_complete():
    result = CambridgeParser(HW_SPAN, url="https://example.com").parse()
    assert set(result.keys()) == {"word", "pos", "pronunciation", "senses", "url"}


def test_parse_url_stored():
    result = CambridgeParser(HW_SPAN, url="https://example.com").parse()
    assert result["url"] == "https://example.com"


def test_parse_url_empty_by_default():
    result = CambridgeParser(HW_SPAN).parse()
    assert result["url"] == ""


# ── Malformed / minimal HTML ──────────────────────────────────────────────


def test_minimal_html_no_crash():
    p = CambridgeParser("<html><body></body></html>")
    assert p.get_headword() == ""
    assert p.get_part_of_speech() == ""
    assert p.get_pronunciation() == {"UK": "", "US": ""}
    assert p.get_senses() == []
    assert p.is_valid_entry() is False


def test_def_block_without_trans_class():
    # A span with "trans" but NOT "dtrans-se" should not be picked up as definition_zh
    html = """<html><body>
    <div class="def-block ddef_block">
      <div class="def ddef_d db">definition only</div>
      <span class="trans dtrans">not the right class</span>
    </div></body></html>"""
    s = CambridgeParser(html).get_senses()[0]
    assert s["definition_zh"] == ""
    assert s["definition_en"] == "definition only"
