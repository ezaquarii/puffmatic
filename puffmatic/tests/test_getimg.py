from os import makedirs
from os.path import isdir, isfile, join
from puffmatic import getimg
from unittest import mock

import pytest
import shutil
import subprocess


@mock.patch("puffmatic.utils.run")
def test_run(run):
    getimg._run(["alfa", "1", "2"])
    assert run.call_count == 1
    assert run.call_args.args == (["alfa", "1", "2"], )
    assert run.call_args.kwargs.get("logger") is not None
    assert run.call_args.kwargs.get("check") is True


def test_download_file(cfg):
    # GIVEN
    #     configured rsync mirror
    #     configured system version and arch
    # WHEN
    #     downloading single file from mirror
    getimg.download_file(mirror=cfg.mirror,
                         version=cfg.version_full,
                         arch=cfg.arch,
                         file="SHA256",
                         output_dir=cfg.img_output_dir)
    # THEN
    #     output directory created
    #     file stored in output directory
    assert isdir(cfg.img_output_dir), "dir not created"
    assert isfile(join(cfg.img_output_dir, "SHA256"))


class TestCheckSha256():
    def test_passed(self, cfg, mirror_dir2):
        # GIVEN
        #     files from OpenBSD distribution
        #     files are not corrupted
        hash_file = "SHA256"
        img_file = "BUILDINFO"
        assert isfile(join(mirror_dir2, hash_file))
        assert isfile(join(mirror_dir2, img_file))

        # WHEN
        #     integrity check of one file
        getimg.check_sha256(working_dir=mirror_dir2,
                            hash_file="SHA256",
                            img_file="BUILDINFO")
        # THEN
        #     passed

    def test_failed(self, cfg, mirror_dir2, tmpdir):
        # GIVEN
        #     SHA256 containing hashes
        #     a file from OpenBSD distribution
        #     the file is damanged
        shutil.copy(src=join(mirror_dir2, "SHA256"),
                    dst=join(tmpdir, "SHA256"))
        with open(join(tmpdir, "BUILDINFO"), "w") as f:
            f.write("forcing sha256 check failure")

        # WHEN
        #     integrity check
        with pytest.raises(subprocess.CalledProcessError) as e:
            getimg.check_sha256(working_dir=tmpdir,
                                hash_file="SHA256",
                                img_file="BUILDINFO")

        # THEN
        #     corruption detected
        assert e.value.returncode == 1


class TestGetimgMain():

    def test_getimg_main(self, cfg):
        # GIVEN
        #      configured mirror
        #      openbsd version
        #      architecture
        # WHEN
        #      image is retrieved
        getimg.getimg_main(cfg=cfg, once=False)

        # THEN
        #      image and sha files in output dir
        #      files match configured openbsd release version
        assert isfile(join(cfg.img_output_dir, "SHA256"))
        assert isfile(join(cfg.img_output_dir,
                           f"install{cfg.version_short}.img"))

    @mock.patch("puffmatic.getimg.download_file")
    def test_skip_download_if_stamp_exists(self, download_file, cfg):
        # GIVEN
        #     mirror stamp exists
        img_stamp_file = join(cfg.img_output_dir,
                              f"install{cfg.version_short}.img.stamp")
        makedirs(cfg.img_output_dir, exist_ok=True)
        with open(img_stamp_file, "w") as f:
            f.write("test stamp")

        # WHEN
        #     download image with "once" option
        rc = getimg.getimg_main(cfg=cfg, once=True)

        # THEN
        #     download skipped
        assert rc == 0
        assert download_file.call_count == 0
