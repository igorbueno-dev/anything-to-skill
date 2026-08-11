from anything_to_skill.verify import (
    find_citations,
    check_traceability,
    extract_quotes,
    cite_check,
    nuance_flags,
    verify_skill,
)


def test_find_citations():
    assert find_citations("x [S1-b0001] y [S2-b0007]") == ["S1-b0001", "S2-b0007"]


def test_orphan_detected(tmp_path):
    d = tmp_path / "sections"
    d.mkdir()
    (d / "t.md").write_text("afirmação [S1-b9999]\n", encoding="utf-8")
    orphans = check_traceability(d, {"S1-b0000": "texto"})
    assert "S1-b9999" in orphans


def test_no_orphans_when_resolvable(tmp_path):
    d = tmp_path / "sections"
    d.mkdir()
    (d / "t.md").write_text("ok [S1-b0000]\n", encoding="utf-8")
    assert check_traceability(d, {"S1-b0000": "texto"}) == []


def test_extract_quotes():
    md = '> "few-shot melhora" [S1-b0001]\n'
    assert extract_quotes(md) == [("few-shot melhora", "S1-b0001")]


def test_cite_check_flags_hallucination():
    idx = {"S1-b0001": "few-shot melhora a acurácia"}
    ok = cite_check([("few-shot melhora", "S1-b0001")], idx)
    bad = cite_check([("nunca dito isso", "S1-b0001")], idx)
    assert ok == []
    assert "S1-b0001" in bad


def test_nuance_flag():
    flags = nuance_flags("few-shot sempre funciona.", "few-shot pode funcionar na maioria dos casos")
    assert flags


def test_verify_writes_report(tmp_path):
    out = tmp_path / "skill"
    (out / "sections").mkdir(parents=True)
    (out / ".qa").mkdir()
    (out / "sections" / "t.md").write_text("ok [S1-b0000]\n", encoding="utf-8")
    p = verify_skill(out, {"S1-b0000": "texto"}, source_texts={"S1": "texto"})
    assert p.name == "verification_report.md"
    assert p.exists()
