from . import fixture_file
from os.path import isfile
import pytest


class TestFixtureFile():

    def test_file_found(self):
        p = fixture_file("bin.txt")
        assert isfile(p)

    def test_file_not_found(self):
        with pytest.raises(AssertionError):
            _ = fixture_file("does-not-exist")
