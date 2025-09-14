import os
from os.path import isdir, isfile, join, exists


class TestCfg():
    def test_output_path_in_temp_directory(self, cfg, tmpdir): # noqa
        paths = (cfg.output_dir,
                 cfg.sets_output_dir,
                 cfg.resp_output_dir,
                 cfg.img_output_dir,
                 cfg.tmp_dir)

        for p in paths:
            common = os.path.commonpath(paths=(p, str(tmpdir)))
            assert common == str(tmpdir), f"{p} not in {tmpdir}"

    def test_templates_from_fixtures_dir(self, cfg):
        assert "fixtures/config/templates" in cfg.templates_dir
        assert exists(join(cfg.templates_dir, "install.yaml"))


def test_hosts_dir(hosts_dir):
    bravo_host_dir = join(hosts_dir, "bravo")
    assert isdir(bravo_host_dir)


def test_templates_dir(templates_dir):
    template_install_conf = join(templates_dir, "install.conf.j2")
    assert isfile(template_install_conf)


def test_tmpdir(work_dir, tmpdir):
    assert str(tmpdir).startswith(work_dir)


def test_mirror(cfg, mirror_dir2):
    stamp = join(mirror_dir2, ".stamp")
    assert isfile(stamp)
    assert mirror_dir2.startswith(cfg.mirror)
