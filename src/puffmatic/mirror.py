"""Mirror module provides OpenBSD pub release directory."""

import logging
import os

from datetime import datetime
from datetime import timezone
from puffmatic import utils

logger = logging.getLogger().getChild(__name__)


def _run(*args, **kwargs):
    kwargs["logger"] = logger
    kwargs["check"] = True
    return utils.run(*args, **kwargs)


def mirror_release_dir(version, arch, output_dir, mirror):
    """Mirror OpenBSD release directory to output_dir."""
    os.makedirs(output_dir, exist_ok=True)
    _run(["openrsync", "-v", "-r", f"{mirror}/{version}/{arch}/", "./"],
         cwd=output_dir)


def check_release_dir(release_dir):
    """Check release directory by running hash check."""
    return _run(["sha256",  "-c", "SHA256"], cwd=release_dir)


def mirror_main(cfg, once, **kwargs):
    """
    Mirror subcommand.

    It downloads OpenBSD release files and places them in output
    directory. Mirror SHA256 is verified as well.
    """
    stamp_file = os.path.join(cfg.sets_output_dir, "mirror.stamp")
    if once and os.path.isfile(stamp_file):
        logger.info(f"found {stamp_file} - skipping")
        return 0

    mirror_release_dir(version=cfg.version_full,
                       arch=cfg.arch,
                       output_dir=cfg.sets_output_dir,
                       mirror=cfg.mirror)
    check_release_dir(cfg.sets_output_dir)
    with open(stamp_file, "w") as f:
        ts = datetime.now(tz=timezone.utc)
        f.write(f"downloaded from {cfg.mirror} at {ts}")
