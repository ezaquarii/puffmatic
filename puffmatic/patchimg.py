"""Patch installer image with auto_install and site sets."""
import logging
import os
import shutil

from os import makedirs
from os.path import abspath, basename, dirname, exists, join, isfile
from puffmatic import utils

logger = logging.getLogger().getChild(__name__)


def _run(*args, **kwargs):
    kwargs["logger"] = logger
    kwargs["check"] = True
    utils.run(*args, **kwargs)


def mount_img(vnd, img_file, mnt_dir):
    """
    Mount image file using vnd.

    This routine requires priviledged access to vnconfig and mount.
    """
    img_dir = dirname(img_file)
    vnd = f"vnd{vnd}"
    _run(["vnconfig", "-v", vnd, img_file],
         cwd=img_dir,
         priv=True)
    _run(["mount", "-o", "noperm", f"/dev/{vnd}a", mnt_dir],
         cwd=img_dir,
         priv=True)


def umount_img(vnd, mnt_dir):
    """Unmount image attached to vnd."""
    _run(["umount", mnt_dir], priv=True)
    _run(["vnconfig", "-v", "-u", f"vnd{vnd}"], priv=True)


def install_file(src, dst, mode):
    """Install file using install utility."""
    _run(["install", "-m", f"0{mode:o}", src, dst], priv=True)


def decompress_file(input_file, output_file, mode=0o644):
    """Decompress file using gzip."""
    with open(output_file, "wb") as ofile:
        _run(["zcat", input_file], stdout=ofile)
    if mode:
        os.chmod(output_file, mode)


def compress_file(input_file, output_file):
    """Decompress file using gzip."""
    with open(output_file, "wb") as ofile:
        _run(["compress", "-9", "-c", input_file], stdout=ofile)


def extract_root_fs(rd_file, root_fs):
    """Extract root fs from bsd ramdisk image."""
    _run(["rdsetroot", "-x", rd_file, root_fs])


def set_root_fs(rd_file, root_fs):
    """Set root fs in ramdisk kernel."""
    _run(["rdsetroot", rd_file, root_fs])


def patch_root_fs(cfg: utils.Config, disklabel_file, response_file, root_fs_file):
    """Mount root fs image and copy installer config files."""
    root_fs_dir = join(cfg.img_output_dir, "mnt", "rd")
    os.makedirs(root_fs_dir, exist_ok=True)
    mount_img(vnd=2, img_file=root_fs_file, mnt_dir=root_fs_dir)
    target_response_file = join(root_fs_dir, "auto_install.conf")
    target_disklabel_file = join(root_fs_dir, "disklabel")
    install_file(src=response_file, dst=target_response_file, mode=0o644)
    if exists(disklabel_file):
        install_file(src=disklabel_file, dst=target_disklabel_file, mode=0o644)
    umount_img(vnd=2, mnt_dir=root_fs_dir)


def patch_bsd_rd(cfg: utils.Config, host_dir, bsd_rd_file):
    """Patch ramdisk file with autoinstall script and sets."""
    bsd_rd_expanded_file = join(cfg.img_output_dir, "bsd.rd.expanded")
    decompress_file(bsd_rd_file, bsd_rd_expanded_file)
    root_fs_file = join(cfg.img_output_dir, "rd.fs")
    extract_root_fs(bsd_rd_expanded_file, root_fs_file)
    disklabel_file = join(host_dir, "disklabel")
    response_file = join(host_dir, "install.conf")
    patch_root_fs(cfg=cfg,
                  disklabel_file=disklabel_file,
                  response_file=response_file,
                  root_fs_file=root_fs_file)
    set_root_fs(bsd_rd_expanded_file, root_fs_file)
    compress_file(bsd_rd_expanded_file, bsd_rd_file)


def patch_boot_conf(host_dir, boot_conf_file):
    """
    Patch /etc/boot.conf to boot from patched bsd.rd.

    It loads host boot.conf if exists and append bsd.rd
    load stanza.
    """
    host_boot_conf = join(host_dir, "boot.conf")
    boot_conf_lines = []
    if isfile(host_boot_conf):
        with open(host_boot_conf, "r") as f:
            boot_conf_lines = [line.strip() for line in f.readlines()]
    boot_conf_lines.append("set image /bsd.rd")
    with open(boot_conf_file, "w") as of:
        content = "\n".join(boot_conf_lines)
        of.write(content)


def copy_site_sets(cfg: utils.Config, hostname, src_sets_dir, dst_sets_dir):
    """
    Copy site set archives from source to dst directory.

    Files are copied only if site sets exist.
    """
    assert hostname
    assert cfg.version_short != (0, 0)
    host_site_tgz = join(src_sets_dir,
                         f"site{cfg.version_short}-{hostname}.tgz")
    site_tgz = join(src_sets_dir,
                    f"site{cfg.version_short}.tgz")
    if isfile(host_site_tgz):
        logger.info(f"copying {host_site_tgz} to {dst_sets_dir}/")
        makedirs(dst_sets_dir, exist_ok=True)
        shutil.copy(host_site_tgz, dst_sets_dir)
    if isfile(site_tgz):
        logger.info(f"copying {site_tgz} to {dst_sets_dir}/")
        makedirs(dst_sets_dir, exist_ok=True)
        shutil.copy(site_tgz, dst_sets_dir)


def patch_img(cfg: utils.Config, host_dir, install_img_file):
    """
    Patch installXY.img installer image.

    1. mount installer img filesystem
    2. add autoinstall script to bsd.rd
    3. copy site sets to tarballs
    """
    hostname = basename(host_dir)
    img_mnt_dir = join(cfg.img_output_dir, "mnt", "img")
    os.makedirs(img_mnt_dir, exist_ok=True)
    mount_img(vnd=1, img_file=install_img_file, mnt_dir=img_mnt_dir)
    bsd_rd = join(img_mnt_dir, "bsd.rd")
    boot_conf = join(img_mnt_dir, "etc", "boot.conf")
    img_sets_dir = join(img_mnt_dir, cfg.version_full, cfg.arch)
    patch_bsd_rd(cfg=cfg,
                 host_dir=host_dir,
                 bsd_rd_file=bsd_rd)
    patch_boot_conf(host_dir=host_dir,
                    boot_conf_file=boot_conf)
    copy_site_sets(cfg=cfg,
                   hostname=hostname,
                   src_sets_dir=cfg.sets_output_dir,
                   dst_sets_dir=img_sets_dir)
    umount_img(vnd=1,
               mnt_dir=img_mnt_dir)


def patchimg_main(cfg, host_dir, **kwargs):
    """
    Patch installer img file with autoinstall script and site sets.

    It requires upstream installXY.img.
    It copies the installer image adding a hostname suffix.
    Then, host-specific installer is patched.
    """
    host_dir = abspath(host_dir)
    hostname = basename(host_dir)
    orig_img_file = join(cfg.img_output_dir,
                         f"install{cfg.version_short}.img")
    host_img_file = join(cfg.img_output_dir,
                         f"install{cfg.version_short}-{hostname}.img")
    if not exists(host_img_file):
        logger.debug(f"copying {orig_img_file} to {host_img_file}")
        shutil.copy(orig_img_file, host_img_file)
    patch_img(cfg=cfg, host_dir=host_dir, install_img_file=host_img_file)


def patchimg_umount_main(cfg, **kwargs):
    """Unmounts image and ramdisk filesystem images."""
    img_mnt_dir = join(cfg.img_output_dir, "mnt", "img")
    rd_mnt_dir = join(cfg.img_output_dir, "mnt", "rd")
    umount_img(vnd=2, mnt_dir=rd_mnt_dir)
    umount_img(vnd=1, mnt_dir=img_mnt_dir)
