import logging

from puffmatic import mirror
from os import listdir, makedirs
from os.path import join
from unittest import mock

logger = logging.getLogger().getChild(__name__)


def test_mirror_release_dir(cfg, mirror_dir2):
    # GIVEN
    #     files stored on mirror server
    mirror_files = set(listdir(mirror_dir2))

    # WHEN
    #     files are downloaded to output dir
    mirror.mirror_release_dir(version=cfg.version_full,
                              arch=cfg.arch,
                              output_dir=cfg.output_dir,
                              mirror=cfg.mirror)

    # THEN
    #     all files from remote directory downloaded
    downloaded_files = set(listdir(cfg.output_dir))
    assert downloaded_files == mirror_files


def test_check_release_dir(cfg, mirror_dir2):
    """
    Check reference mirror fixture directory.

    Since the mirrored directory is a golden sample,
    check should pass.
    """
    assert mirror.check_release_dir(mirror_dir2) == 0


class TestMirrorMain():

    def test_mirror_main(self, cfg, mirror_dir2):
        # GIVEN
        #     mirror with openbsd release
        mirror_files = set(listdir(mirror_dir2))

        # WHEN
        #     release files mirrored into local directory
        mirror.mirror_main(cfg=cfg, once=False)

        # THEN
        #     all files downloaded
        #     integrity check passed
        #     stamp created
        downloaded_files = set(listdir(cfg.sets_output_dir))
        assert mirror_files.issubset(downloaded_files)
        assert "mirror.stamp" in downloaded_files

    @mock.patch("puffmatic.mirror.mirror_release_dir")
    def test_skip_download_if_stamp_exists(self, mirror_release_dir, cfg):
        # GIVEN
        #     mirror stamp exists
        stamp_file = join(cfg.sets_output_dir, "mirror.stamp")
        makedirs(cfg.sets_output_dir, exist_ok=True)
        with open(stamp_file, "w") as f:
            f.write("test stamp")

        # WHEN
        #     mirror with "once" option
        rc = mirror.mirror_main(cfg=cfg, once=True)

        # THEN
        #     download skipped
        assert rc == 0
        assert mirror_release_dir.call_count == 0
