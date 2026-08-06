from anything_to_skill.structure import segment_by_headings, segment_index_for_line


def test_splits_on_headings():
    md = "# A\nlinha a1\nlinha a2\n\n# B\nlinha b1\n"
    segs = segment_by_headings(md)
    assert [s.heading for s in segs] == ["A", "B"]
    assert segs[0].start_line == 1
    assert segs[0].level == 1


def test_preamble_before_first_heading():
    md = "intro sem titulo\n\n# A\ncorpo\n"
    segs = segment_by_headings(md)
    assert segs[0].heading == "(preambulo)"
    assert segs[1].heading == "A"


def test_no_headings_single_segment():
    md = "so texto\noutra linha\n"
    segs = segment_by_headings(md)
    assert len(segs) == 1
    assert segs[0].word_count == 4


def test_segment_index_for_line():
    md = "# A\na1\n# B\nb1\n"
    segs = segment_by_headings(md)
    assert segment_index_for_line(segs, 2) == 0  # a1 na secao A
    assert segment_index_for_line(segs, 4) == 1  # b1 na secao B
    assert segment_index_for_line(segs, 999) == -1
