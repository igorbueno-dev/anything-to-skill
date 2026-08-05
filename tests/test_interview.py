import json

from anything_to_skill.interview import normalize_answers, write_config, BuildConfig


def test_defaults_when_empty():
    cfg = normalize_answers({})
    assert cfg.depth == "reference"
    assert cfg.authoritative == []


def test_rejects_bad_depth_falls_back():
    cfg = normalize_answers({"depth": "hardcore"})
    assert cfg.depth == "reference"


def test_accepts_valid_study_depth():
    cfg = normalize_answers({"depth": "study", "authoritative": "S1"})
    assert cfg.depth == "study"
    assert cfg.authoritative == ["S1"]


def test_writes_config(tmp_path):
    cfg = BuildConfig(purpose="study", depth="study", scope="prompting", authoritative=["S1"])
    p = write_config(cfg, tmp_path)
    assert json.loads(p.read_text(encoding="utf-8"))["authoritative"] == ["S1"]
