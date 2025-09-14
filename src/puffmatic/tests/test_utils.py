import logging
import pytest
import subprocess

from puffmatic import utils
from puffmatic.tests import fixture_file
from os.path import (abspath, dirname, join)
from unittest import mock
from urllib.parse import urlparse


class TestCreateLogger():

    def test_root_logger(self):
        logger = utils.create_logger()
        assert logger.name == "root"

    def test_create_named_logger(self):
        logger = utils.create_logger("a.b.c")
        assert logger.name == "a.b.c"


class TestCmdOutputLogger():

    stdout_lines = ["stdout 1", "stdout 2", "stdout 3"]
    stderr_lines = ["stderr 1", "stderr 2", "stderr 3", "stderr 4"]

    @pytest.fixture
    def logger(self):
        return mock.Mock(spec=logging.Logger)

    @pytest.fixture
    def stdout_file(self, tmp_path):
        stdout_file = tmp_path / "stdout.txt"
        stdout_file.write_text("\n".join(self.stdout_lines))
        return stdout_file

    @pytest.fixture
    def stderr_file(self, tmp_path):
        stdout_file = tmp_path / "stderr.txt"
        stdout_file.write_text("\n".join(self.stderr_lines))
        return stdout_file

    def test_no_logger(self, stdout_file):
        with open(stdout_file, "r") as f:
            utils._cmd_output_logger(logger=None, stdout=stdout_file)

    def test_reads_all_data(self, logger, stdout_file, stderr_file):
        all_output_lines = self.stdout_lines + self.stderr_lines
        with (open(stdout_file, "r") as stdout,
              open(stderr_file, "r") as stderr):
            utils._cmd_output_logger(logger=logger,
                                     stdout=stdout,
                                     stderr=stderr)
        assert logger.info.call_count == len(all_output_lines)
        expected_info_calls = [mock.call(line) for line in all_output_lines]
        logger.info.assert_has_calls(expected_info_calls, any_order=True)


class TestFormatCmd():

    def test_command_and_args(self):
        r = utils._format_cmd(["foo", "arg1", "arg2"])
        assert r == "foo arg1 arg2"

    def test_stdout_redirection(self):
        with open("/dev/null", "w") as f:
            r = utils._format_cmd(["foo", "arg1", "arg2"], stdout=f)
        assert r == "foo arg1 arg2 > /dev/null"

    def test_stdin_redirection(self):
        with open("/dev/null", "r") as f:
            r = utils._format_cmd(["foo", "arg1", "arg2"], stdin=f)
        assert r == "foo arg1 arg2 < /dev/null"

    def test_stderr_redirection(self):
        with open("/dev/null", "r") as f:
            r = utils._format_cmd(["foo", "arg1", "arg2"], stderr=f)
        assert r == "foo arg1 arg2 2> /dev/null"


class TestParseVersion():

    def test_valid_version(self):
        v = utils.parse_version("7.6")
        assert v == (7, 6)

    def test_not_a_version(self):
        invalid_versions = ["abc",
                            "a.b",
                            "7.",
                            "7",
                            ".",
                            "..",
                            "1.2.3",
                            "7.a",
                            "a.7"]
        for v in invalid_versions:
            assert not utils.parse_version(v)

    def test_parsing_version_tuple(self):
        v = utils.parse_version((7, 6))
        assert v == (7, 6)


class TestRun():

    @pytest.fixture
    def run_sh(self):
        return fixture_file("utils/run.sh")

    @pytest.fixture
    def logger(self):
        logger = mock.Mock(spec=logging.Logger)
        logger.getChild.return_value = logger
        return logger

    def test_run_captures_stdout(self, run_sh, logger):
        rc = utils.run([run_sh, "stdout"], logger=logger)
        logger.getChild.assert_called_with("run_sh")
        assert rc == 0
        assert logger.info.call_count == 2

    def test_run_captures_stdout_stderr(self, run_sh, logger):
        rc = utils.run([run_sh, "stdout+stderr"], logger=logger)
        logger.getChild.assert_called_with("run_sh")
        assert rc == 0
        assert logger.info.call_count == 4

    def test_return_exit_value(self, run_sh, logger):
        rc = utils.run([run_sh, "fail"], logger=logger)
        assert rc == 1

    def test_raise_when_command_fails(self, run_sh, logger):
        with pytest.raises(subprocess.CalledProcessError):
            utils.run([run_sh, "fail"], logger=logger, check=True)

    def test_no_logger(self, run_sh):
        rc = utils.run([run_sh, "fail"])
        assert rc == 1


def test_load_yaml():
    a = fixture_file("utils/a.yaml")
    b = fixture_file("utils/b.yaml")
    value = utils.load_yaml(a, b)
    assert value == dict(alfa=1,
                         bravo=2,
                         charlie=4,
                         delta=5,
                         echo=6,
                         foxtrot=7)


class TestConfig():

    @pytest.fixture
    def config(self):
        config1_file = fixture_file("utils/config1.yaml")
        config1 = utils.Config.load(config1_file)
        return config1

    def test_load(self, config):
        assert config.version == (7, 6)
        assert config.arch == "amd64"
        assert config.mirror == "rsync://mirror.planetunix.net"
        assert config.install_server == "http://install.example.com"
        assert config.install_basic_auth == "user:password"
        assert config.install_server_dir == "sets"
        assert config.templates_dir == abspath("templates")
        assert config.output_dir == abspath("output")
        assert config.hostname is None
        assert config.ssh_public_key is None
        assert config.root_password is None
        assert config.disk_encryption_passphrase is None
        assert config.ipv6_address is None
        assert config.ipv6_gateway is None

    def test_update(self, config):
        config2_file = fixture_file("utils/config2.yaml")
        config = config.update(config2_file)
        assert config.version == (7, 6)
        assert config.arch == "amd64"
        assert config.mirror == "rsync://mirror.planetunix.net"
        assert config.install_server == "http://install.example.com"
        assert config.install_basic_auth == "user:password"
        assert config.install_server_dir == "sets"
        assert config.templates_dir == abspath("templates")
        assert config.output_dir == abspath("output")
        assert config.hostname == "test-hostname"
        assert config.ssh_public_key == "test-ssh-key"
        assert config.root_password == "test-password"
        assert config.disk_encryption_passphrase == "test-passphrase"
        assert config.ipv6_address == "2001:db8::1"
        assert config.ipv6_gateway == "fe80::1%vio0"

    def test_load_fails(self):
        non_existing_file = join(dirname(__file__), "does-not-exist")
        with pytest.raises(FileNotFoundError):
            utils.Config.load(non_existing_file)

    def test_version_full_str(self, config):
        assert config.version_full == "7.6"

    def test_version_short_str(self, config):
        assert config.version_short == "76"

    def test_resp_server_url(self, config: utils.Config):
        u = urlparse(config.install_server)
        assert f"{u.scheme}://{config.install_basic_auth}@" in config.resp_server_url
        assert u.netloc in config.resp_server_url

    def test_resp_server_url_without_basic_auth(self, config):
        config.install_basic_auth = ""
        assert "@" not in config.resp_server_url

    def test_to_dict(self, config):
        d = config.to_dict()
        assert d["version_full"] == "7.6"
        assert d["version_short"] == "76"
        assert d["sets_output_dir"] == config.sets_output_dir
        assert d["resp_output_dir"] == config.resp_output_dir
        assert d["resp_server_url"] == config.resp_server_url
        assert d["disklabel_server_url"] == config.disklabel_server_url
        assert d["install_server_dir"] == config.install_server_dir
        assert d["tmp_dir"] == config.tmp_dir
