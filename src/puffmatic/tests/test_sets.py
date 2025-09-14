import tarfile

from puffmatic import sets
from unittest import mock

from os.path import basename, dirname, join, exists


@mock.patch("puffmatic.utils.run")
def test_run(run):
    sets._run(["alfa", "1", "2"])
    assert run.call_count == 1
    assert run.call_args.args == (["alfa", "1", "2"], )
    assert run.call_args.kwargs.get("logger") is not None
    assert run.call_args.kwargs.get("check") is True


@mock.patch("puffmatic.utils.run")
def test_test_mount_tmp_dir(run, tmpdir):
    sets.mount_tmp_dir(tmp_dir=tmpdir, size=128)
    assert run.call_args.kwargs.get("priv") is True
    assert any("-s128M" in str(arg) for arg in run.call_args.args[0])


@mock.patch("puffmatic.utils.run")
def test_umount_tmp_dir(run, tmpdir):
    sets.umount_tmp_dir(tmp_dir=tmpdir)
    assert run.call_args.kwargs.get("priv") is True


@mock.patch("puffmatic.utils.run")
def test_run_mtree(run, tmpdir):
    site_dir = tmpdir / "site"
    mtree_file = tmpdir / "site.mtree"
    sets.run_mtree(site_dir=site_dir, mtree_file=mtree_file)
    assert run.call_args.kwargs.get("cwd") == site_dir


@mock.patch("puffmatic.utils.run")
def test_create_tarball(run, tmpdir):
    site_dir = tmpdir / "site"
    output_file = tmpdir / "arch.tgz"
    sets.create_tarball(site_dir, output_file)
    assert run.call_args.kwargs.get("cwd") == site_dir


def test_update_index(tmpdir):
    import pathlib
    pathlib.Path(tmpdir / "alfa").touch()
    pathlib.Path(tmpdir / "bravo").touch()
    sets.update_index(tmpdir)
    with open(tmpdir / "index.txt") as f:
        index = f.read()
        assert "alfa" in index
        assert "bravo" in index


def test_create_site_set(cfg, hosts_dir, tmpdir):
    # GIVEN
    #     site dir with mtree spec
    site_dir = join(hosts_dir, "example", "site")
    mtree_file = join(hosts_dir, "example", "site.mtree")

    # WHEN
    #     site archive is created
    sets.create_site_set(site_dir=site_dir,
                         mtree_file=mtree_file,
                         output_dir=cfg.sets_output_dir,
                         archive="site77.tgz",
                         tmp_dir=tmpdir)
    site_archive = join(cfg.sets_output_dir, "site77.tgz")

    # THEN
    #     archive is placed in sets directory
    #     archive is compressed
    #     it contains all files
    #     mode modified before archiving
    assert exists(site_archive)
    with tarfile.open(site_archive, "r:gz") as tar:
        members = tar.getmembers()
        files = [m.name for m in members]
        assert "./etc/ssh/ssh_host_rsa_key" in files
        assert "./etc/ssh/ssh_host_rsa_key.pub" in files
        assert "./etc/ssh/ssh_host_ecdsa_key" in files
        assert "./etc/ssh/ssh_host_ecdsa_key.pub" in files
        assert "./etc/ssh/ssh_host_ed25519_key" in files
        assert "./etc/ssh/ssh_host_ed25519_key.pub" in files

        for m in members:
            if m.name.endswith("_key"):
                assert (m.mode & 0o777) == 0o600
            if m.name.endswith("_key.pub"):
                assert (m.mode & 0o777) == 0o644


class TestHostSiteSetMain():

    def test_no_host_dir(self, cfg, tmpdir):
        # GIVEN
        #     host site directory does not exist
        import pytest
        cfg.hostname = "non-existing-host"
        non_existing_host_dir = join(tmpdir, "non-existing-host")

        # WHEN
        #     attempting to create host site set
        with pytest.raises(SystemExit) as se:
            sets.host_site_set_main(cfg=cfg,
                                    host_dir=non_existing_host_dir)

        # THEN
        #     no action
        #     graceful exit
        assert se.value.code == 0

    def test_set_file_created(self, cfg, hosts_dir, tmpdir):
        # GIVEN
        #     host exists with site dir
        cfg.hostname = "example"
        host_dir = join(hosts_dir, "example")

        # WHEN
        #     creating host site set
        sets.host_site_set_main(cfg=cfg, host_dir=host_dir)

        # THEN
        #     archive is placed in output directory
        #     host suffix
        #     version in short format
        set_archive = f"site{cfg.version_short}-{cfg.hostname}.tgz"
        set_archive_path = join(cfg.sets_output_dir, set_archive)
        assert exists(set_archive_path)


def test_site_set_main(cfg, hosts_dir, tmpdir):
    # GIVEN
    #     domain site dir exists
    site_dir = join(hosts_dir, "example", "site")

    # WHEN
    #     creating site set
    sets.site_set_main(cfg=cfg,
                       site_dir=site_dir)

    # THEN
    #     site archive created
    #     no hostname suffx
    #     version in short format
    site_archive_path = join(cfg.sets_output_dir,
                             f"site{cfg.version_short}.tgz")
    assert exists(site_archive_path)
