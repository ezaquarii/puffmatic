import os

__dir = os.path.dirname(__file__)
fixtures_dir = os.path.join(__dir, "fixtures")


def fixture_file(p):
    """Return fixture file, if exists."""
    file_path = os.path.join(fixtures_dir, p)
    if not os.path.exists(file_path):
        raise AssertionError(f"no {p} in fixture")
    return file_path
