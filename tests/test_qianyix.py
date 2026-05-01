"""Robustness tests for clidict.parsers.qianyix."""

from clidict.parsers.qianyix import QianyixParser, _extract_stress, _text


# ── _text helper ──────────────────────────────────────────────────────────

def _el(html_str: str):
    from lxml import html as lxml_html
    return lxml_html.fromstring(html_str)


def test_text_none():
    assert _text(None) == ""

def test_text_collapses_whitespace():
    assert _text(_el("<p>  hello   world  </p>")) == "hello world"

def test_text_nested():
    assert _text(_el("<div>а <b>б</b> в</div>")) == "а б в"

def test_text_empty():
    assert _text(_el("<p></p>")) == ""


# ── _extract_stress ───────────────────────────────────────────────────────

def test_extract_stress_plain_word():
    el = _el("<h2>привет</h2>")
    assert _extract_stress(el) == "привет"

def test_extract_stress_one_mark():
    # пока<b>з</b>ать → пока́зать
    el = _el("<h2>пока<b>з</b>ать</h2>")
    result = _extract_stress(el)
    assert "з́" in result
    assert result == "показ́ать"   # з + combining acute

def test_extract_stress_multiple_marks():
    el = _el("<h2><b>б</b>уква <b>а</b>лфавита</h2>")
    result = _extract_stress(el)
    assert result.count("́") == 2

def test_extract_stress_b_with_tail():
    el = _el("<h2>го<b>в</b>орить!</h2>")
    result = _extract_stress(el)
    assert result.endswith("!")
    assert "́" in result

def test_extract_stress_no_b_tags():
    el = _el("<h2>слово</h2>")
    assert _extract_stress(el) == "слово"

def test_extract_stress_empty():
    el = _el("<h2></h2>")
    assert _extract_stress(el) == ""

def test_extract_stress_whitespace_normalized():
    el = _el("<h2>  при  <b>в</b>ет  </h2>")
    result = _extract_stress(el)
    assert "  " not in result


# ── HTML fixtures ─────────────────────────────────────────────────────────

def _parser(html: str) -> QianyixParser:
    return QianyixParser(html, word="тест")


BASE_FULL = """<html><body>
<div class="col-md-7">
  <div id="base0" class="panel panel-default baseword">
    <div class="panel-body view">
      <h2 class="keyword">го<b>в</b>орить</h2>
      <p class="exp">说话 · 讲述</p>
    </div>
  </div>
  <div id="detail0" class="panel panel-default subs">
    <div class="panel-body">
      <div class="row">
        <div>医学</div><div>表示，显示</div>
      </div>
    </div>
  </div>
  <div id="example0" class="panel panel-default example">
    <div class="panel-body">
      <p>他在说话。</p>
      <p>Он говорит.</p>
      <p>我们谈谈吧。</p>
      <p>Давайте поговорим.</p>
    </div>
  </div>
  <div id="grm0" class="panel panel-default">
    <div class="panel-body">
      <div class="grammardiv">变位变格
        <h2>现在时</h2>
        <h3>单数</h3>
        <table>
          <tr><th></th><th>形式</th></tr>
          <tr><td>1人称</td><td>говорю</td></tr>
        </table>
      </div>
    </div>
  </div>
</div>
</body></html>"""

NO_ENTRY_HTML = """<html><body>
<p>没有找到词条</p>
</body></html>"""

EMPTY_BASE_HTML = """<html><body>
<div id="base0" class="panel panel-default baseword">
  <div class="panel-body view">
  </div>
</div>
</body></html>"""


# ── is_valid_entry ────────────────────────────────────────────────────────

def test_is_valid_entry_true():
    assert _parser(BASE_FULL).is_valid_entry() is True

def test_is_valid_entry_false():
    assert _parser(NO_ENTRY_HTML).is_valid_entry() is False

def test_is_valid_entry_empty_html():
    assert _parser("<html><body></body></html>").is_valid_entry() is False


# ── get_headword ──────────────────────────────────────────────────────────

def test_get_headword_from_keyword():
    hw = _parser(BASE_FULL).get_headword()
    assert "в́" in hw   # stress mark on в

def test_get_headword_fallback_to_word():
    p = _parser(NO_ENTRY_HTML)
    assert p.get_headword() == "тест"

def test_get_headword_uses_first_keyword():
    html = """<html><body>
      <h2 class="keyword">пер<b>в</b>ый</h2>
      <h2 class="keyword">вт<b>о</b>рой</h2>
    </body></html>"""
    hw = _parser(html).get_headword()
    assert "в́" in hw
    assert "о́" not in hw


# ── get_bases / _parse_one_entry ──────────────────────────────────────────

def test_get_bases_full_entry():
    bases = _parser(BASE_FULL).get_bases()
    assert len(bases) == 1
    b = bases[0]
    assert "说话" in " · ".join(b["definitions"])
    assert b["industries"][0]["field"] == "医学"
    assert len(b["examples"]) == 2
    assert b["examples"][0]["zh"] == "他在说话。"
    assert b["examples"][0]["ru"] == "Он говорит."
    assert len(b["conjugations"]) == 1
    assert "单数" in b["conjugations"][0]["label"]

def test_get_bases_empty_filtered():
    # base div with no definitions or conjugations → filtered out
    assert _parser(EMPTY_BASE_HTML).get_bases() == []

def test_get_bases_two_entries():
    html = """<html><body>
      <div id="base0" class="panel panel-default baseword">
        <div class="panel-body view">
          <h2 class="keyword">сл<b>о</b>во</h2>
          <p class="exp">词语</p>
        </div>
      </div>
      <div id="base1" class="panel panel-default baseword">
        <div class="panel-body view">
          <h2 class="keyword">фр<b>а</b>за</h2>
          <p class="exp">短语</p>
        </div>
      </div>
    </body></html>"""
    bases = _parser(html).get_bases()
    assert len(bases) == 2
    assert bases[0]["definitions"] == ["词语"]
    assert bases[1]["definitions"] == ["短语"]

def test_base_stops_at_next_base():
    # examples/subs AFTER base1 should not be mixed into base0
    html = """<html><body>
      <div id="base0" class="panel panel-default baseword">
        <div class="panel-body view">
          <h2 class="keyword">сл<b>о</b>во</h2>
          <p class="exp">词语</p>
        </div>
      </div>
      <div id="base1" class="panel panel-default baseword">
        <div class="panel-body view">
          <h2 class="keyword">фр<b>а</b>за</h2>
          <p class="exp">短语</p>
        </div>
      </div>
      <div id="example1" class="panel panel-default example">
        <div class="panel-body">
          <p>短语的例句。</p>
          <p>Пример фразы.</p>
        </div>
      </div>
    </body></html>"""
    bases = _parser(html).get_bases()
    assert bases[0]["examples"] == []
    assert bases[1]["examples"][0]["ru"] == "Пример фразы."


# ── _parse_industries ─────────────────────────────────────────────────────

def test_parse_industries_normal():
    html = """<html><body>
      <div id="base0" class="panel panel-default baseword">
        <div class="panel-body view">
          <h2 class="keyword">сл<b>о</b>во</h2>
          <p class="exp">词</p>
        </div>
      </div>
      <div id="detail0" class="panel panel-default subs">
        <div class="panel-body">
          <div class="row"><div>法律</div><div>法律术语</div></div>
          <div class="row"><div>医学</div><div>医学术语</div></div>
        </div>
      </div>
    </body></html>"""
    bases = _parser(html).get_bases()
    inds = bases[0]["industries"]
    assert len(inds) == 2
    assert inds[0] == {"field": "法律", "zh": "法律术语"}

def test_parse_industries_incomplete_row_skipped():
    html = """<html><body>
      <div id="base0" class="panel panel-default baseword">
        <div class="panel-body view">
          <h2 class="keyword"><b>а</b></h2>
          <p class="exp">字母</p>
        </div>
      </div>
      <div id="detail0" class="panel panel-default subs">
        <div class="panel-body">
          <div class="row"><div>只有一列</div></div>
          <div class="row"><div>两列</div><div>正常</div></div>
        </div>
      </div>
    </body></html>"""
    bases = _parser(html).get_bases()
    assert len(bases[0]["industries"]) == 1


# ── _parse_examples ───────────────────────────────────────────────────────

def _make_example_html(paragraphs: list[str]) -> str:
    ps = "".join(f"<p>{p}</p>" for p in paragraphs)
    return f"""<html><body>
      <div id="base0" class="panel panel-default baseword">
        <div class="panel-body view">
          <h2 class="keyword"><b>а</b></h2><p class="exp">字母</p>
        </div>
      </div>
      <div id="example0" class="panel panel-default example">
        <div class="panel-body">{ps}</div>
      </div>
    </body></html>"""


def test_parse_examples_pairs():
    html = _make_example_html(["中文一。", "Русский один.", "中文二。", "Русский два."])
    ex = _parser(html).get_bases()[0]["examples"]
    assert len(ex) == 2
    assert ex[0] == {"zh": "中文一。", "ru": "Русский один."}
    assert ex[1] == {"zh": "中文二。", "ru": "Русский два."}

def test_parse_examples_odd_count_safe():
    # Odd number of paragraphs — last one dropped silently
    html = _make_example_html(["中文。", "Русский.", "孤例。"])
    ex = _parser(html).get_bases()[0]["examples"]
    assert len(ex) == 1

def test_parse_examples_empty():
    html = _make_example_html([])
    assert _parser(html).get_bases()[0]["examples"] == []

def test_parse_examples_number_lines_filtered():
    # Standalone "1." lines should be skipped
    html = _make_example_html(["1.", "中文。", "Русский.", "2."])
    ex = _parser(html).get_bases()[0]["examples"]
    assert len(ex) == 1
    assert ex[0]["zh"] == "中文。"

def test_parse_examples_max_limit():
    # More than MAX_EXAMPLES (5) pairs → capped at 5
    paragraphs = []
    for i in range(8):
        paragraphs += [f"中文{i}。", f"Русский {i}."]
    html = _make_example_html(paragraphs)
    ex = _parser(html).get_bases()[0]["examples"]
    assert len(ex) == 5


# ── _parse_conjugation / _extract_table_rows ─────────────────────────────

CONJ_HTML = """<html><body>
  <div id="base0" class="panel panel-default baseword">
    <div class="panel-body view">
      <h2 class="keyword">го<b>в</b>орить</h2>
      <p class="exp">说</p>
    </div>
  </div>
  <div id="grm0" class="panel panel-default">
    <div class="panel-body">
      <div class="grammardiv">变位变格
        <h2>主动语态</h2>
        <h3>现在时</h3>
        <table>
          <tr><th></th><th>单数</th><th>复数</th></tr>
          <tr><td>1人称</td><td>говорю</td><td>говорим</td></tr>
          <tr><td>2人称</td><td>говоришь</td><td>говорите</td></tr>
        </table>
        <h3>过去时</h3>
        <table>
          <tr><th>阳性</th><th>阴性</th></tr>
          <tr><td>говорил</td><td>говорила</td></tr>
        </table>
      </div>
    </div>
  </div>
</body></html>"""

def test_conjugation_multiple_h3():
    bases = _parser(CONJ_HTML).get_bases()
    conjs = bases[0]["conjugations"]
    assert len(conjs) == 2
    assert "主动语态" in conjs[0]["label"]
    assert "现在时" in conjs[0]["label"]
    assert "过去时" in conjs[1]["label"]

def test_conjugation_table_rows():
    bases = _parser(CONJ_HTML).get_bases()
    rows = bases[0]["conjugations"][0]["rows"]
    # Header row + 2 data rows
    assert len(rows) == 3
    assert rows[0] == ["", "单数", "复数"]
    assert rows[1][1] == "говорю"

def test_conjugation_empty_panel():
    html = """<html><body>
      <div id="base0" class="panel panel-default baseword">
        <div class="panel-body view">
          <h2 class="keyword"><b>а</b></h2><p class="exp">字母</p>
        </div>
      </div>
      <div id="grm0" class="panel panel-default">
        <div class="panel-body"><div class="grammardiv">变位变格</div></div>
      </div>
    </body></html>"""
    # No tables → conjugations list is empty → base filtered out (no defs either)
    # Actually this base HAS definitions ("字母"), so it IS included but conjugations empty
    bases = _parser(html).get_bases()
    assert bases[0]["conjugations"] == []

def test_extract_table_rows_ragged():
    html = """<html><body>
      <div id="base0" class="panel panel-default baseword">
        <div class="panel-body view">
          <h2 class="keyword"><b>а</b></h2><p class="exp">字母</p>
        </div>
      </div>
      <div id="grm0" class="panel panel-default">
        <div class="panel-body"><div class="grammardiv">变位变格
          <h3>变格</h3>
          <table>
            <tr><th>A</th><th>B</th><th>C</th></tr>
            <tr><td>1</td><td>2</td></tr>
            <tr><td>X</td></tr>
          </table>
        </div></div>
      </div>
    </body></html>"""
    conjs = _parser(html).get_bases()[0]["conjugations"]
    rows = conjs[0]["rows"]
    assert rows[0] == ["A", "B", "C"]
    assert rows[1] == ["1", "2"]
    assert rows[2] == ["X"]


# ── parse() contract ──────────────────────────────────────────────────────

def test_parse_keys():
    result = _parser(BASE_FULL).parse()
    assert set(result.keys()) == {"word", "bases"}

def test_parse_word_has_stress():
    result = _parser(BASE_FULL).parse()
    assert "́" in result["word"]

def test_parse_bases_is_list():
    result = _parser(BASE_FULL).parse()
    assert isinstance(result["bases"], list)


# ── Edge cases ────────────────────────────────────────────────────────────

def test_minimal_html_no_crash():
    p = _parser("<html><body></body></html>")
    assert p.get_headword() == "тест"
    assert p.get_bases() == []
    assert p.is_valid_entry() is False

def test_base_id_with_dash_ignored():
    # id="base-foo" should NOT be treated as a base div
    html = """<html><body>
      <div id="base-foo" class="panel panel-default baseword">
        <div class="panel-body view">
          <h2 class="keyword"><b>а</b></h2><p class="exp">字母</p>
        </div>
      </div>
    </body></html>"""
    assert _parser(html).get_bases() == []
