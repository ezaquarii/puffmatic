"""Disklabel generator."""

import logging

from os import makedirs
from os.path import (abspath,
                     exists,
                     basename,
                     join)
from shutil import copyfile
from sys import exit


logger = logging.getLogger().getChild(__name__)


def disklabel_main(cfg, host_dir, **kwargs):
    """Copy disklabel file to installation media directory."""
    host_dir = abspath(host_dir)
    output_dir = abspath(cfg.resp_output_dir)
    templates_dir = abspath(cfg.templates_dir)
    hostname = basename(host_dir)
    host_disklabel_file = join(host_dir, "disklabel")
    generic_disklabel_file = join(templates_dir, "disklabel")
    output_disklabel_file = join(output_dir, f"disklabel-{hostname}")
    makedirs(output_dir, exist_ok=True)
    if exists(host_disklabel_file):
        logger.info((f"copying {host_disklabel_file} "
                     f"to {output_disklabel_file}"))
        copyfile(host_disklabel_file, output_disklabel_file)
    elif exists(generic_disklabel_file):
        logger.info((f"copying {generic_disklabel_file} "
                     f"to {output_disklabel_file}"))
        copyfile(generic_disklabel_file, output_disklabel_file)
    else:
        logger.error("no disklabel file or template found")
        exit(1)
