import pytest
import filecmp

from os.path import join, isfile
from puffmatic.disklabel import disklabel_main


class TestDisklabelMain():

    def test_copy_host_disklabel_file(self, cfg, hosts_dir):
        # GIVEN
        #     host config has custom disklabel
        host = join(hosts_dir, "example")
        src_disklabel = join(host, "disklabel")
        dst_disklabel = join(cfg.resp_output_dir, "disklabel-example")

        # WHEN
        #     disklabel is copied
        disklabel_main(cfg, host)

        # THEN
        #     disklabel is copied from host dir to output dir
        #     disklabel has host name suffix
        assert isfile(dst_disklabel)
        assert "-example" in dst_disklabel
        assert filecmp.cmp(src_disklabel, dst_disklabel)

    def test_copy_generic_disklabel_file(self, cfg, tmpdir):
        # GIVEN
        #     host has no disklabel
        #     generic disklabel exists
        host = join(tmpdir, "labelless")
        src_disklabel = join(cfg.templates_dir, "disklabel")
        dst_disklabel = join(cfg.resp_output_dir, "disklabel-labelless")

        # WHEN
        #     disklabel is copied
        disklabel_main(cfg, host)

        # THEN
        #     generic disklabel is copied
        #     file has hostname suffix
        assert isfile(dst_disklabel)
        assert "-labelless" in dst_disklabel
        assert filecmp.cmp(src_disklabel, dst_disklabel)

    def test_no_disklabel_found(self, cfg, tmpdir):
        # WHEN
        #     host has no disklabel
        #     no generic disklabel
        host = join(tmpdir, "non-existing")
        cfg.templates_dir = join(tmpdir, "non-existing")

        # WHEN
        #     disklabel copied
        with pytest.raises(SystemExit) as se:
            disklabel_main(cfg, host)

        # THEN
        #     exit with error
        assert se.value.code == 1
