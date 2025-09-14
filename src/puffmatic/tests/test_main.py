import logging
import os
import shutil
import sys
import pytest

from puffmatic.__main__ import load_config, main
from contextlib import contextmanager
from unittest import mock


@contextmanager
def _chdir(path):
    original_cwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(original_cwd)


class TestLoadConfig():

    def test_load_config(self, config_file):
        c = load_config(config_file)
        assert c.install_server == "http://install.example.com"

    def test_load_config_from_cwd(self, config_file, tmp_path):
        shutil.copy(config_file, tmp_path)
        with _chdir(tmp_path):
            c = load_config(None)
        assert c.install_server == "http://install.example.com"

    def test_cannot_load_file(self, tmp_path):
        with _chdir(tmp_path):
            with pytest.raises(RuntimeError) as e:
                _ = load_config(None)
        assert str(e.value) == "no config file provided"


class TestMain():

    def setup_method(self):
        self.args = sys.argv

    def teardown_method(self):
        sys.argv = self.args

    def test_help(self, capsys):
        main(["help"])
        captured = capsys.readouterr()
        assert "usage:" in captured.out

    def test_config_load_failed(self):
        # GIVEN
        #     config file cannot be loaded
        args = ["--config", "does-not-exist", "env"]

        # WHEN
        #     run command
        rc = main(args)

        # THEN
        #     failure
        #     root cause logged
        assert rc == 1

    def test_load_config(self, capsys, config_file):
        # GIVEN
        #     valid config
        args = ["--config", config_file, "env"]

        # WHEN
        #     env called
        rc = main(args)

        # THEN
        #     success
        #     config parsed
        #     config printed to stdout
        assert rc == 0
        captured = capsys.readouterr()
        assert "install.example.com" in captured.out

    def test_verbose_mode(self, caplog, config_file):
        # GIVEN
        #     verbose mode enabled
        args = ["--config", config_file, "--verbose", "env"]

        # WHEN
        #     help is printed
        main(args)

        # THEN
        #     logger prints debug message
        assert caplog.records[0].levelno == logging.DEBUG
        assert caplog.records[0].message == "debug is enabled"

    @mock.patch("puffmatic.__main__.mirror_main")
    def test_mirror(self, mirror_main, cfg, config_file):
        args = ["--config", config_file, "mirror"]
        main(args)
        c = mirror_main.call_args.args[0]
        assert c.install_server == cfg.install_server

    @mock.patch("puffmatic.__main__.host_site_set_main")
    def test_host_site_set_main(self, host_site_set_main,
                                cfg, hosts_dir, config_file):
        host_dir = os.path.join(hosts_dir, "bravo")
        main(["--config", config_file, "host-site-set", "-H", host_dir])
        args = host_site_set_main.call_args.args
        kwargs = host_site_set_main.call_args.kwargs
        assert args[0].version_short == "77"
        assert kwargs["host_dir"] == host_dir

    @mock.patch("puffmatic.__main__.site_set_main")
    def test_site_set_main(self, site_set_main,
                           cfg, hosts_dir, config_file):
        site_dir = os.path.join(hosts_dir, "bravo")
        main(["--config", config_file, "site-set", "--site-dir", site_dir])
        args = site_set_main.call_args.args
        kwargs = site_set_main.call_args.kwargs
        assert args[0].version_short == "77"
        assert kwargs["site_dir"] == site_dir

    @mock.patch("puffmatic.__main__.disklabel_main")
    def test_disklabel(self, disklabel_main, hosts_dir, config_file):
        host_dir = os.path.join(hosts_dir, "bravo")
        args = ["--config", config_file, "disklabel", "--host-dir", host_dir]
        main(args)
        kwargs = disklabel_main.call_args.kwargs
        assert host_dir == kwargs["host_dir"]

    @mock.patch("puffmatic.__main__.response_main")
    def test_response(self, response_main, hosts_dir, config_file):
        host_dir = os.path.join(hosts_dir, "bravo")
        args = ["--config", config_file, "response", "--host-dir", host_dir]
        main(args)
        kwargs = response_main.call_args.kwargs
        assert host_dir == kwargs["host_dir"]

    @mock.patch("puffmatic.__main__.getimg_main")
    def test_getimg(self, getimg_main, config_file):
        args = ["--config", config_file, "getimg"]
        main(args)
        args = getimg_main.call_args.args
        assert args[0].version_short == "77"

    @mock.patch("puffmatic.__main__.patchimg_main")
    def test_patchimg(self, patchimg_main, hosts_dir, config_file):
        host_dir = os.path.join(hosts_dir, "bravo")
        args = ["--config", config_file, "patchimg", "--host-dir", host_dir]
        main(args)
        args = patchimg_main.call_args.args
        kwargs = patchimg_main.call_args.kwargs
        assert args[0].version_short == "77"
        assert kwargs["host_dir"] == host_dir

    @mock.patch("puffmatic.__main__.patchimg_umount_main")
    def test_patchimg_umount(self, getimg_umount_main, config_file):
        args = ["--config", config_file, "patchimg-umount"]
        main(args)
        assert getimg_umount_main.call_count == 1
