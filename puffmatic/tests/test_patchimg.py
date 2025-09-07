import gzip
import pytest
import shutil

from tempfile import TemporaryDirectory
from os.path import dirname, exists, isfile, join
from os import makedirs
from unittest import mock

from . import fixture_file
from puffmatic.patchimg import compress_file, decompress_file, patch_boot_conf
from puffmatic import patchimg


@mock.patch("puffmatic.utils.run")
def test_mount_img(run, tmpdir):
    mnt_dir = join(tmpdir, "mnt")
    img_file = join(tmpdir, "install.img")
    patchimg.mount_img(vnd=1,
                       img_file=img_file,
                       mnt_dir=mnt_dir)
    assert run.call_count == 2
    vnconfig = run.call_args_list[0]
    assert vnconfig.kwargs["priv"] is True
    assert vnconfig.kwargs["cwd"] == dirname(img_file)
    assert vnconfig.kwargs["check"] is True
    assert vnconfig.kwargs["logger"]

    mount = run.call_args_list[1]
    assert mount.kwargs["priv"] is True
    assert mount.kwargs["cwd"] == dirname(img_file)
    assert mount.kwargs["check"] is True
    assert mount.kwargs["logger"]


@mock.patch("puffmatic.utils.run")
def test_umount_img(run, tmpdir):
    mnt_dir = join(tmpdir, "mnt")
    patchimg.umount_img(vnd=1,
                        mnt_dir=mnt_dir)
    assert run.call_count == 2
    vnconfig = run.call_args_list[0]
    assert vnconfig.kwargs["priv"] is True
    assert vnconfig.kwargs["check"] is True
    assert vnconfig.kwargs["logger"]

    umount = run.call_args_list[1]
    assert umount.kwargs["priv"] is True
    assert umount.kwargs["check"] is True
    assert umount.kwargs["logger"]


@mock.patch("puffmatic.utils.run")
def test_install_file(run):
    src = "/tmp/source.txt"
    dst = "/mnt/target.txt"
    mode = 0o644
    patchimg.install_file(src=src, dst=dst, mode=mode)
    install = run.call_args_list[0]
    assert install.kwargs["priv"] is True
    assert "0644" in install.args[0]


def test_decompress_file():
    input_file = fixture_file("patchimg/sample.txt.gz")
    ref_file = fixture_file("patchimg/sample.txt")

    with TemporaryDirectory() as tmp:
        output_file = join(tmp, "output.txt")
        decompress_file(input_file, output_file)
        with open(output_file, "rb") as f, open(ref_file, "rb") as rf:
            assert f.read() == rf.read()


def test_compress_file():
    input_file = fixture_file("patchimg/sample.txt")

    with TemporaryDirectory() as tmp:
        output_file_gz = join(tmp, "output.txt.gz")
        compress_file(input_file, output_file_gz)
        with (open(input_file, "r") as ref_file,
              gzip.open(output_file_gz, "rb") as compressed_file):
            assert ref_file.read() == compressed_file.read().decode("utf-8")


@mock.patch("puffmatic.utils.run")
def test_extract_root_fs(run):
    rd_file = "/tmp/bsd.rd"
    root_fs = "/tmp/bsd.fs"
    patchimg.extract_root_fs(rd_file=rd_file, root_fs=root_fs)
    install = run.call_args_list[0]
    assert "-x" in install.args[0]
    assert install.kwargs["logger"] is not None
    assert install.kwargs["check"] is True


@mock.patch("puffmatic.utils.run")
def test_set_root_fs(run):
    rd_file = "/tmp/bsd.rd"
    root_fs = "/tmp/bsd.fs"
    patchimg.set_root_fs(rd_file=rd_file, root_fs=root_fs)
    install = run.call_args_list[0]
    assert "-x" not in install.args[0]
    assert install.kwargs["logger"] is not None
    assert install.kwargs["check"] is True


class TestPatchBootConf():

    @pytest.fixture
    def boot_conf_file(self, tmpdir):
        return tmpdir / "boot.conf"

    @pytest.fixture
    def host_dir(self):
        boot_conf = fixture_file("patchimg/boot.conf")
        return dirname(boot_conf)

    def test_image_appended_to_host_boot_conf(self, host_dir, boot_conf_file):
        patch_boot_conf(host_dir, boot_conf_file=boot_conf_file)
        with open(boot_conf_file, "r") as f:
            lines = [line.strip() for line in f.readlines()]
        assert "stty com0 115200" in lines
        assert "set tty com0" in lines
        assert "set image /bsd.rd" == lines[-1]

    def test_no_host_boot_conf(self, tmpdir, boot_conf_file):
        empty = tmpdir / "empty"
        makedirs(empty)
        patch_boot_conf(host_dir=empty, boot_conf_file=boot_conf_file)
        with open(boot_conf_file, "r") as f:
            lines = [line.strip() for line in f.readlines()]
        assert ["set image /bsd.rd"] == lines


def test_copy_site_sets(cfg, tmp_path):
    # GIVEN
    #     general site set
    #     host specific site set
    src_dir = join(tmp_path, "src_sets")
    makedirs(src_dir)
    sets = [f"site{cfg.version_short}.tgz",
            f"site{cfg.version_short}-{cfg.hostname}.tgz"]
    for s in sets:
        spath = join(src_dir, s)
        with open(spath, "w") as f:
            f.write("dummy site set archive")

    # WHEN
    #     sets copied to destination directory
    patchimg.copy_site_sets(cfg=cfg,
                            hostname=cfg.hostname,
                            src_sets_dir=src_dir,
                            dst_sets_dir=cfg.sets_output_dir)
    # THEN
    #     both sets copied
    for s in sets:
        spath = join(cfg.sets_output_dir, s)
        assert isfile(spath)


class TestPatchImgMain():

    def teardown_method(self, *args):
        """
        Unmount images and deactive vnd devices.

        Under normal operation vnd should be cleaned by the code under
        test. However, if the test fails, cleanup is prevented by
        exception. Attempt cleanup first (skipping errors), then
        verify if vnd devices are deactived.
        """
        from subprocess import run
        for vnd in ["vnd1", "vnd2"]:
            run(["doas", "umount", f"/dev/{vnd}"], check=False)
            run(["doas", "vnconfig", "-u", vnd], check=False)
        for vnd in ("vnd1", "vnd2"):
            vnd_chk = run(["doas", "vnconfig", "-l", vnd],
                          capture_output=True).stdout
            assert f"{vnd}: not in use" in str(vnd_chk), f"/dev/{vnd} active"

    def test_patchimg_main(self, cfg, hosts_dir, mirror_dir2):
        # GIVEN
        #     installXY.img downloaded into img directory
        #     host configuration present
        mirror_install_img = join(mirror_dir2,
                                  f"install{cfg.version_short}.img")
        assert isfile(mirror_install_img)
        host_dir = join(hosts_dir, "example")
        orig_install_img = join(cfg.img_output_dir,
                                f"install{cfg.version_short}.img")
        makedirs(cfg.img_output_dir)
        shutil.copy(mirror_install_img, orig_install_img)

        # WHEN
        #     patching installXY.img
        patchimg.patchimg_main(cfg=cfg,
                               host_dir=host_dir)

        # THEN
        #     original image not changed
        #     patched host specific image created
        patched_install_img = join(cfg.img_output_dir,
                                   f"install{cfg.version_short}-example.img")
        assert exists(patched_install_img)


@mock.patch("puffmatic.patchimg.umount_img")
def test_patchimg_umount_main(umount_img, cfg):
    # WHEN
    #     umount cleanup called
    patchimg.patchimg_umount_main(cfg)
    # THEN
    #     vnds are unmounted in reverse order
    first = umount_img.call_args_list[0].kwargs["vnd"]
    second = umount_img.call_args_list[1].kwargs["vnd"]
    assert first > second
