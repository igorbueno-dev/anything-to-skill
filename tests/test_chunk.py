from anything_to_skill.chunk import chunk_markdown, annotate


def test_splits_into_blocks():
    md = "# Título\n\nPrimeiro parágrafo.\n\nSegundo parágrafo.\n"
    blocks = chunk_markdown(md, "S1")
    assert [b.anchor for b in blocks] == ["S1-b0000", "S1-b0001", "S1-b0002"]
    assert blocks[1].text == "Primeiro parágrafo."


def test_annotate_embeds_anchor_comments():
    md = "Parágrafo único.\n"
    blocks = chunk_markdown(md, "S1")
    out = annotate(md, blocks)
    assert "{#S1-b0000}" in out
    assert "Parágrafo único." in out


def test_anchors_stable_across_runs():
    md = "a\n\nb\n"
    assert [x.anchor for x in chunk_markdown(md, "S1")] == \
           [x.anchor for x in chunk_markdown(md, "S1")]


def test_block_records_start_line():
    md = "linha0\n\nlinha2\n\nlinha4\n"
    blocks = chunk_markdown(md, "S1")
    assert blocks[0].line == 1
    assert blocks[1].line == 3
    assert blocks[2].line == 5
