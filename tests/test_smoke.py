import anything_to_skill


def test_package_imports_and_has_version():
    assert isinstance(anything_to_skill.__version__, str)
    assert anything_to_skill.__version__
