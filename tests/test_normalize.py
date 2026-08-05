from pathlib import Path

from anything_to_skill.normalize import normalize


def test_markdown_passthrough(tmp_path):
    p = tmp_path / "a.md"
    p.write_text("# T\n\ncorpo\n", encoding="utf-8")
    doc = normalize(p, kind="md", out_images_dir=tmp_path / "fig", source_id="S1")
    assert doc.markdown == "# T\n\ncorpo\n"
    assert doc.images == []


def test_txt_passthrough(tmp_path):
    p = tmp_path / "a.txt"
    p.write_text("linha um\nlinha dois\n", encoding="utf-8")
    doc = normalize(p, kind="txt", out_images_dir=tmp_path / "fig", source_id="S1")
    assert "linha um" in doc.markdown


def test_html_to_markdown(tmp_path):
    doc = normalize(tmp_path / "x.html", kind="html",
                    out_images_dir=tmp_path / "fig", source_id="S1",
                    html_text="<h1>Título</h1><p>corpo</p>")
    assert "Título" in doc.markdown
    assert "corpo" in doc.markdown


def test_pdf_extracts_and_anchors_images(tmp_path):
    pdf = Path(__file__).parent / "fixtures" / "two_col.pdf"
    doc = normalize(pdf, kind="pdf", out_images_dir=tmp_path / "fig", source_id="S1")
    assert len(doc.images) >= 1
    img = doc.images[0]
    assert (tmp_path / "fig" / img.filename).exists()
    assert f"]({img.filename}" in doc.markdown or f"](figures/{img.filename}" in doc.markdown
    # texto da página também presente
    assert "Few-shot" in doc.markdown
