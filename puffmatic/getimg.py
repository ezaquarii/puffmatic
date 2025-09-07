"""Download installer image files."""
import logging
import os

from puffmatic import utils
from datetime import datetime, timezone


logger = logging.getLogger().getChild(__name__)


def _run(*args, **kwargs):
    kwargs["logger"] = logger
    kwargs["check"] = True
    utils.run(*args, **kwargs)


def download_file(mirror, version, arch, file, output_dir):
    """Download a file from OpenBSD rsync mirror."""
    os.makedirs(output_dir, exist_ok=True)
    _run(["openrsync", "-v", f"{mirror}/{version}/{arch}/{file}", "./"],
         cwd=output_dir)


def check_sha256(working_dir, hash_file, img_file):
    """Check installer image by running hash check."""
    _run(["sha256", "-C", hash_file, img_file], cwd=working_dir)


def getimg_main(cfg, once, **kwargs):
    """
    Get installer image subcommand.

    It downloads OpenBSD USB installer image and places it in output
    directory. SHA256 is verified as well.
    """
    img_file = f"install{cfg.version_short}.img"
    sha_file = "SHA256"
    img_stamp_file = os.path.join(cfg.img_output_dir,
                                  f"{img_file}.stamp")
    if once and os.path.isfile(img_stamp_file):
        logger.info(f"found {img_stamp_file} - skipping")
        return 0
    for file in [img_file, "SHA256"]:
        download_file(mirror=cfg.mirror,
                      version=cfg.version_full,
                      arch=cfg.arch,
                      file=file,
                      output_dir=cfg.img_output_dir)
    check_sha256(working_dir=cfg.img_output_dir,
                 hash_file=sha_file,
                 img_file=img_file)
    with open(img_stamp_file, "w") as f:
        ts = datetime.now(tz=timezone.utc)
        f.write(f"downloaded from {cfg.mirror} at {ts}")
