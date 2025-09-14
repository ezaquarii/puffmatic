from puffmatic import response
from unittest import mock

from os.path import exists, join
from os import makedirs

import filecmp
import pytest


@mock.patch("puffmatic.utils.run")
def test_run(run):
    response._run(["alfa", "1", "2"])
    assert run.call_count == 1
    assert run.call_args.args == (["alfa", "1", "2"], )
    assert run.call_args.kwargs.get("logger") is not None
    assert run.call_args.kwargs.get("check") is True


class TestRenderInstallResp():

    def test_copy_hardcoded_response_file(self, cfg, hosts_dir, tmpdir):
        # GIVEN
        #     host configuration has hardcoded autoinstall config
        #     config has trailing newline
        #     output directory exists
        autoinstall_file = join(hosts_dir, "example", "install.conf")
        assert exists(autoinstall_file)
        with open(autoinstall_file) as f:
            assert f.read()[-1] == '\n'
        autoinstall_output_file = join(cfg.resp_output_dir, "install.conf")
        makedirs(cfg.resp_output_dir)

        # WHEN
        #     config rendered
        response.render_install_resp(install_resp_template=autoinstall_file,
                                     output_file=autoinstall_output_file,
                                     context=vars(cfg))

        # THEN
        #     file is copied
        #     trailing whitespace is retained
        assert filecmp.cmp(autoinstall_file, autoinstall_output_file)

    def test_render_from_template(self, cfg, templates_dir, tmpdir):
        # GIVEN
        #     host has autoinstall jinja template
        template_file = join(templates_dir, "install.conf.j2")
        assert exists(template_file)
        output_file = join(cfg.resp_output_dir, "auto_install.conf")

        # WHEN
        #     response rendered
        response.render_install_resp(install_resp_template=template_file,
                                     output_file=output_file,
                                     context=vars(cfg))

        # THEN
        #     template filled with data from host config
        with open(output_file, "r") as f:
            rendered = f.read()
        assert len(rendered) > 0
        assert f"System hostname = {cfg.hostname}" in rendered


class TestResponseMain():

    def test_host_harcoded_response(self, cfg, hosts_dir):
        host_dir = join(hosts_dir, "example")
        response.response_main(cfg, host_dir)
        output_file = join(cfg.resp_output_dir, "install-example.conf")
        assert exists(output_file)
        with open(output_file) as f:
            rendered = f.read()
            assert "System hostname = example" in rendered
            assert "Host hardcoded = yes" in rendered

    def test_host_template_response(self, cfg, hosts_dir):
        # GIVEN
        #     host config has response template
        cfg.hostname = "bravo"
        host_dir = join(hosts_dir, "bravo")
        host_template = join(host_dir, "install.conf.j2")
        assert exists(host_template)

        # WHEN
        #     autoinstall config rendered
        response.response_main(cfg, host_dir)

        # THEN
        #     file placed in response file directory
        #     template filled with data from host config
        #     template came from host config directory
        output_file = join(cfg.resp_output_dir, "install-bravo.conf")
        assert exists(output_file)
        with open(output_file) as f:
            rendered = f.read()
            assert "System hostname = bravo" in rendered
            assert "Bravo host template = yes" in rendered

    def test_use_generic_response(self, cfg, hosts_dir):
        # GIVEN
        #     host configuration without resp or template
        #     default template exists
        cfg.hostname = "charlie"
        host_dir = join(hosts_dir, "charlie")

        # WHEN
        #     response rendered
        response.response_main(cfg, host_dir)
        output_file = join(cfg.resp_output_dir, "install-charlie.conf")

        # THEN
        #     file rendered from default template
        assert exists(output_file)
        with open(output_file) as f:
            rendered = f.read()
            assert "System hostname = charlie" in rendered
            assert "Default template = yes" in rendered

    def test_missing_response_template(self, cfg, hosts_dir, tmpdir):
        # GIVEN
        #     no response file
        #     no respones file template
        cfg.hostname = "empty"
        cfg.templates_dir = join(tmpdir, "empty")
        empty_host_dir = join(hosts_dir, "empty")

        # WHEN
        #     response rendered
        with pytest.raises(SystemExit) as e:
            response.response_main(cfg, empty_host_dir)

        # THEN
        #     exit with error code
        assert e.value.code == 1
