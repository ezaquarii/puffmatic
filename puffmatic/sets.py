"""Site set generator."""

import logging
import os

from puffmatic import utils
from os.path import (abspath,
                     basename,
                     isdir,
                     join)
import shutil
import sys


logger = logging.getLogger().getChild(__name__)


def _run(*args, **kwargs):
    kwargs["logger"] = logger
    kwargs["check"] = True
    utils.run(*args, **kwargs)


def mount_tmp_dir(tmp_dir, size=64):
    """Mount temporary directory where sets can be created."""
    _run(["mount", "-t", "mfs", "-o", f"noperm,-s{size}M", "swap", tmp_dir],
         priv=True)


def umount_tmp_dir(tmp_dir):
    """Umount temporary directory."""
    _run(["umount", "-f", str(tmp_dir)], priv=True)


def run_mtree(site_dir, mtree_file):
    """Run mtree to fix any site set files deviations."""
    _run(["mtree", "-f", mtree_file, "-U"],
         cwd=site_dir)


def create_tarball(site_dir, output_file):
    """Create site set tarball."""
    _run(["tar", "-c", "-z", "-f", output_file, "."],
         cwd=site_dir)


def update_index(dir):
    """Update index.txt using bsd ls command."""
    index = os.path.join(dir, "index.txt")
    with open(index, "wb") as f:
        _run(["ls", "-l"],
             cwd=dir,
             stdout=f)


def create_site_set(site_dir, mtree_file, output_dir, archive, tmp_dir):
    """Create siteXY.tgz or siteXY-$host.tgz file."""
    site_archive = join(output_dir, archive)
    site_dir_copy = join(tmp_dir, basename(site_dir))
    shutil.copytree(src=site_dir,
                    dst=site_dir_copy)
    run_mtree(site_dir_copy, mtree_file)
    logger.info(f"creating {site_archive}")
    os.makedirs(output_dir, exist_ok=True)
    create_tarball(site_dir_copy, site_archive)
    logger.info(f"updating index in {output_dir}")
    update_index(output_dir)


def host_site_set_main(cfg, host_dir, **kwargs):
    """Generate siteXY-{hostname}.tgz tarballs."""
    host_dir = abspath(host_dir)
    hostname = basename(host_dir)
    archive = f"site{cfg.version_short}-{hostname}.tgz"
    host_site_dir = join(host_dir, "site")
    host_mtree_file = join(host_dir, "site.mtree")
    sets_output_dir = abspath(cfg.sets_output_dir)

    if not isdir(host_site_dir):
        logger.info(f"no site for host {hostname} - skipping")
        sys.exit(0)

    os.makedirs(cfg.sets_output_dir, exist_ok=True)
    os.makedirs(cfg.tmp_dir, exist_ok=True)
    mount_tmp_dir(cfg.tmp_dir, size=32)
    create_site_set(site_dir=host_site_dir,
                    mtree_file=host_mtree_file,
                    output_dir=sets_output_dir,
                    archive=archive,
                    tmp_dir=cfg.tmp_dir)
    umount_tmp_dir(cfg.tmp_dir)


def site_set_main(cfg, site_dir, **kwargs):
    """Generate siteXY.tgz tarball."""
    site_dir = abspath(site_dir)
    mtree_file = abspath(join(site_dir, "..", "site.mtree"))
    sets_output_dir = abspath(cfg.sets_output_dir)
    archive = f"site{cfg.version_short}.tgz"
    os.makedirs(cfg.sets_output_dir, exist_ok=True)
    os.makedirs(cfg.tmp_dir, exist_ok=True)
    mount_tmp_dir(cfg.tmp_dir, size=32)
    create_site_set(site_dir=site_dir,
                    mtree_file=mtree_file,
                    output_dir=sets_output_dir,
                    archive=archive,
                    tmp_dir=cfg.tmp_dir)
    umount_tmp_dir(cfg.tmp_dir)
