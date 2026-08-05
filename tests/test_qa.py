from anything_to_skill.qa import (
    broken_word_ratio,
    encoding_artifact_ratio,
    layout_score,
    text_yield,
    image_fidelity,
    assess,
    write_qa_report,
    retry_extraction,
)


def test_clean_prose_scores_high():
    t = "Few-shot prompting works well.\n\nIt improves accuracy in many tasks.\n"
    assert broken_word_ratio(t) > 0.9
    assert encoding_artifact_ratio(t) == 1.0
    assert layout_score(t) == 1.0


def test_column_merge_flagged():
    t = "Few- shot prom pting w orks in man y tas ks acr oss doma ins"
    assert broken_word_ratio(t) < 0.7


def test_encoding_garbage_flagged():
    t = "he�llo cid:44 /CIDFont wor�ld"
    assert encoding_artifact_ratio(t) < 0.8


def test_collapsed_layout():
    assert layout_score("tudo numa linha so sem paragrafo nenhum aqui") < 1.0


def test_image_fidelity():
    assert image_fidelity(0, 3) < 1.0
    assert image_fidelity(3, 3) == 1.0
    assert image_fidelity(0, None) == 1.0


def test_clean_status():
    r = assess("S1", "Boa prosa completa.\n\nOutro paragrafo aqui inteiro.\n", pages=1)
    assert r.status == "clean"


def test_failed_on_garbage():
    r = assess("S2", "he�llo cid:44 w o r l d", pages=10)
    assert r.status == "failed"
    assert r.flags


def test_writes_report(tmp_path):
    r = assess("S1", "ok completo aqui.\n\nmais texto.\n", pages=1)
    p = write_qa_report([r], tmp_path)
    assert p.name == "extraction_report.md"
    assert "S1" in p.read_text(encoding="utf-8")


def test_retry_prefers_clean(tmp_path):
    from anything_to_skill.normalize import NormalizedDoc
    bad = lambda *a, **k: NormalizedDoc(markdown="he�llo cid:44 w o r l d")
    good = lambda *a, **k: NormalizedDoc(markdown="Boa prosa completa.\n\nParagrafo inteiro aqui.\n")
    doc, report = retry_extraction(tmp_path / "x.pdf", "pdf", [bad, good],
                                   tmp_path / "fig", "S1")
    assert report.status == "clean"
    assert "Boa prosa" in doc.markdown
