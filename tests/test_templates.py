from anything_to_skill.templates import render_section


def test_paper_template_headers():
    s = render_section("paper", "Atenção", [{"label": "self-attention", "citation": "[S1-b0001]"}])
    assert "# Atenção" in s
    assert "## Achados" in s
    assert "[S1-b0001]" in s


def test_article_differs_from_paper():
    a = render_section("article", "T", [])
    p = render_section("paper", "T", [])
    assert a != p
    assert "## Tese" in a


def test_reference_is_flat_list():
    s = render_section("reference", "Termos", [{"label": "API", "citation": "[S1-b0000]"}])
    assert "## " not in s  # sem cabeçalhos de schema
    assert "API" in s


def test_unknown_profile_falls_back_to_article():
    assert "## Tese" in render_section("weird", "T", [])
