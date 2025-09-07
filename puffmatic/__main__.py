"""Main."""
import argparse
import logging
import os.path
import sys

from puffmatic.disklabel import disklabel_main
from puffmatic.mirror import mirror_main
from puffmatic.response import response_main
from puffmatic.sets import host_site_set_main, site_set_main
from puffmatic.getimg import getimg_main
from puffmatic.patchimg import patchimg_main, patchimg_umount_main
from puffmatic.utils import Config, create_logger


logger = create_logger()


def load_config(config_file="config.yaml") -> Config:
    if config_file:
        return Config.load(config_file)
    elif os.path.exists("config.yaml"):
        return Config.load("config.yaml")
    else:
        raise RuntimeError("no config file provided")


def main(args):
    """Execute main body."""
    args_formatter = argparse.ArgumentDefaultsHelpFormatter
    parser = argparse.ArgumentParser(
        description='Process some commands.',
        formatter_class=args_formatter,
        prog="puffmatic"
    )
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--config", "-c", type=str)
    subpar = parser.add_subparsers(dest='command', required=True)

    _ = subpar.add_parser("help", help="Display help")

    mirror_parser = subpar.add_parser("mirror",
                                      formatter_class=args_formatter,
                                      help="Mirror OpenBSD release directory")

    mirror_parser.add_argument("--once", "-1",
                               action="store_true",
                               help=("Mirror only once and stamp directory. "
                                     "Do not re-download if stamp exists."))

    host_site_set_parser = subpar.add_parser("host-site-set",
                                             formatter_class=args_formatter,
                                             help="Create host site set archive.")
    host_site_set_parser.add_argument("--host-dir", "-H",
                                      type=str,
                                      required=True,
                                      help="Directory with host site set content")

    site_set_parser = subpar.add_parser("site-set",
                                        formatter_class=args_formatter,
                                        help="Create site set archive.")
    site_set_parser.add_argument("--site-dir", "-d",
                                 type=str,
                                 required=True,
                                 help="Directory with common site set content")

    disklabel_parser = subpar.add_parser("disklabel",
                                         formatter_class=args_formatter,
                                         help="Generate disklabel file")
    disklabel_parser.add_argument("--host-dir", "-H",
                                  type=str,
                                  required=True,
                                  help="directory with host configuration")

    response_parser = subpar.add_parser("response",
                                        formatter_class=args_formatter,
                                        help="Generate response file")
    response_parser.add_argument("--host-dir", "-H",
                                 type=str,
                                 required=True,
                                 help="directory with host configuration")

    getimg_parser = subpar.add_parser("getimg",
                                      formatter_class=args_formatter,
                                      help="Download installer image")
    getimg_parser.add_argument("--once", "-1",
                               action="store_true",
                               help=("Download image once and stamp it. "
                                     "Do not re-download if stamp exists."))

    patchimg_parser = subpar.add_parser("patchimg",
                                        formatter_class=args_formatter,
                                        help="Patch installer image")
    patchimg_parser.add_argument("--host-dir", "-H",
                                 type=str,
                                 required=True,
                                 help="directory with host configuration")

    _ = subpar.add_parser("patchimg-umount",
                          help="umount any installer image left by patchimg")

    _ = subpar.add_parser("env", help="print config and environment")

    args = parser.parse_args(args=args)
    kwargs = vars(args)
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("debug is enabled")
    if args.command == "help":
        parser.print_help()
        return 0

    try:
        cfg = load_config(args.config)
    except BaseException as e:
        logger.error(e)
        return 1

    if args.command == "mirror":
        mirror_main(cfg, **vars(args))
    elif args.command == "host-site-set":
        host_site_set_main(cfg, **vars(args))
    elif args.command == "site-set":
        site_set_main(cfg, **vars(args))
    elif args.command == "disklabel":
        disklabel_main(cfg, **vars(args))
    elif args.command == "response":
        response_main(cfg, **vars(args))
    elif args.command == "getimg":
        getimg_main(cfg, **vars(args))
    elif args.command == "patchimg":
        patchimg_main(cfg, **kwargs)
    elif args.command == "patchimg-umount":
        patchimg_umount_main(cfg)
    else:
        print(vars(cfg))
        return 0


if __name__ == "__main__":  # pragma: nocover
    rc = main(args=sys.argv[1:])
    sys.exit(rc)
