"""Provide fixtures for all tests."""
import os
import pytest
import subprocess
import puffmatic.utils


__dir = os.path.dirname(__file__)
__data_dir = os.path.join(__dir, "data")
__fixtures_dir = os.path.join(__dir, "fixtures")


def pytest_addoption(parser):
    """Configure custom options to enable custom test behavior."""
    parser.addoption("--run-integration",
                     action="store_true",
                     default=False,
                     help="run integration tests against real resources")
    parser.addoption("--work-dir",
                     action="store",
                     default="/release/puffmatic/",
                     help="tests working directory")


def pytest_configure(config):
    """Configure pytest runner."""
    basetemp = os.path.join(config.option.work_dir, "tmp")
    config.option.basetemp = basetemp


@pytest.fixture
def work_dir(pytestconfig):
    """
    Test suite working directory.

    Working directory contains temp directory as well
    as dynamically generated fixture data.
    """
    return pytestconfig.option.work_dir


@pytest.fixture
def mirror_dir2(work_dir, cfg):  # pragma: nocover
    """
    Directory containing mirrored OpenBSD release.

    This fixture lives outside temporary directory so it will
    be persisted between test run invocation. Mirroring entire
    release is time consuming and require several GBs of disk space.
    """
    mirror_dir = os.path.join(work_dir, "mirror", "OpenBSD",
                              cfg.version_full, cfg.arch) + os.sep
    stamp_file = os.path.join(mirror_dir, ".stamp")
    if os.path.isfile(stamp_file):
        return mirror_dir
    src = ("rsync://mirror.planetunix.net/OpenBSD/"
           f"{cfg.version_full}/{cfg.arch}")
    os.makedirs(mirror_dir, exist_ok=True)
    assert mirror_dir.endswith("/")
    subprocess.run(["openrsync", "-v", "-r", src, mirror_dir],
                   cwd=mirror_dir,
                   check=True)
    with open(stamp_file, "w") as f:
        f.write("stamp")
    return mirror_dir


@pytest.fixture
def config_file():
    config_yaml = os.path.join(__fixtures_dir, "config", "config.yaml")
    assert os.path.isfile(config_yaml)
    return config_yaml


@pytest.fixture
def cfg(tmpdir, work_dir):
    """
    Load generator config fixture.

    Output directory resides in temporary directory.
    Temporary directory will be deleted after test run.

    Templates directory points to fixture directory. Do not
    modify templates directory.
    """
    config_yaml = os.path.join(__fixtures_dir, "config", "config.yaml")
    assert os.path.exists(config_yaml)
    cfg = puffmatic.utils.Config.load(config_yaml)
    cfg.hostname = "example"
    cfg.output_dir = os.path.join(tmpdir, "output")
    os.makedirs(cfg.output_dir, exist_ok=True)
    cfg.templates_dir = os.path.join(__fixtures_dir, "config", "templates")
    mirror_dir = os.path.join(work_dir, "mirror", "OpenBSD")
    cfg.mirror = mirror_dir
    return cfg


@pytest.fixture
def hosts_dir():
    """Return path to host configurations."""
    return os.path.join(__fixtures_dir, "config", "hosts")


@pytest.fixture
def templates_dir():
    """Return path to test templates directory."""
    return os.path.join(__fixtures_dir, "config", "templates")
