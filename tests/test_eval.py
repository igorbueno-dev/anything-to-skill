import json
from pathlib import Path

from anything_to_skill.eval import evaluate_skill, write_eval_report


def _skill(tmp_path):
    skill = tmp_path / "skill"
    (skill / ".graph").mkdir(parents=True)
    (skill / ".graph" / "anchors.json").write_text(
        json.dumps({"S1-b0000": "texto"}), encoding="utf-8")
    (skill / "content").mkdir()
    (skill / "content" / "S1.md").write_text("texto\n", encoding="utf-8")
    return skill


def test_evaluate_scores(tmp_path):
    skill = _skill(tmp_path)

    def qa_gen(content):
        return [{"question": "q1", "expected_anchor": "S1-b0000"},
                {"question": "q2", "expected_anchor": "S1-b0000"}]

    def answer(q, sd):
        if q == "q1":
            return {"answer": "ok", "cited_anchors": ["S1-b0000"]}  # grounded + esperado
        return {"answer": "chute", "cited_anchors": ["S9-bad"]}      # nao ancorado

    rep = evaluate_skill(skill, qa_gen_fn=qa_gen, answer_fn=answer)
    assert rep.total == 2
    assert rep.correct == 1          # so q1 cita ancora valida
    assert rep.cited_expected == 1   # so q1 cita a ancora esperada


def test_write_eval_report(tmp_path):
    skill = _skill(tmp_path)

    def qa_gen(content):
        return [{"question": "q1", "expected_anchor": "S1-b0000"}]

    def answer(q, sd):
        return {"answer": "ok", "cited_anchors": ["S1-b0000"]}

    rep = evaluate_skill(skill, qa_gen_fn=qa_gen, answer_fn=answer)
    p = write_eval_report(rep, skill / ".qa")
    assert p.exists()
    txt = p.read_text(encoding="utf-8")
    assert "1/1" in txt
