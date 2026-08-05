from anything_to_skill.profiles import classify, refine_with


def test_detects_paper():
    t = "Abstract\nWe study X.\n...\nReferences\n[1] Foo et al. 2020. doi:10.1/x"
    assert classify(t, "pdf") == "paper"


def test_detects_transcript():
    t = "00:12 Alice: bem-vindos\n00:45 Bob: obrigado por virem"
    assert classify(t, "txt") == "transcript"


def test_detects_technical_book():
    t = "## 3.2 Loops\n\n```python\nfor i in range(10):\n    pass\n```\n\n## 3.3\n\n```py\nx=1\n```"
    assert classify(t, "md") == "technical_book"


def test_default_article():
    assert classify("Uma opiniao fluida sobre o tema, sem estrutura formal.", "html") == "article"


def test_refine_without_refiner_returns_base():
    assert refine_with("texto", "article", None) == "article"


def test_refine_with_refiner_overrides():
    assert refine_with("texto", "article", lambda t: "paper") == "paper"
