"""Utilities to generate response file."""
import jinja2
import logging
import os
import shutil
import sys

from puffmatic import utils
from os import makedirs
from os.path import (abspath,
                     basename,
                     exists,
                     dirname,
                     join)


logger = logging.getLogger().getChild(__name__)


def _run(*args, **kwargs):
    kwargs["logger"] = logger
    kwargs["check"] = True
    utils.run(*args, **kwargs)


def render_install_resp(install_resp_template: str,
                        output_file: str,
                        context):
    """
    Render host response file from template and context.

    File is passed through Jinja only if it ends with .j2 extension.
    Otherwise file is copied verbatim.
    """
    if not install_resp_template.endswith(".j2"):
        shutil.copy(install_resp_template, output_file)
    else:
        template_dir = dirname(install_resp_template)
        template_name = basename(install_resp_template)
        loader = jinja2.FileSystemLoader(searchpath=template_dir)
        env = jinja2.Environment(loader=loader, keep_trailing_newline=True)
        template = env.get_template(template_name)
        os.makedirs(dirname(output_file), exist_ok=True)
        with open(output_file, "w") as f:
            txt = template.render(**context)
            f.write(txt)


def response_main(cfg, host_dir, **kwargs):
    """Render autoinstall response file."""
    host_dir = abspath(host_dir)
    templates_dir = abspath(cfg.templates_dir)
    output_dir = abspath(cfg.resp_output_dir)

    makedirs(output_dir, exist_ok=True)
    hostname = basename(host_dir)
    output_file = join(output_dir, f"install-{hostname}.conf")
    host_install_resp = join(host_dir, "install.conf")
    host_install_resp_template = join(host_dir, "install.conf.j2")
    host_install_resp_config = join(host_dir, "install.yaml")
    generic_install_resp_template = join(templates_dir, "install.conf.j2")
    generic_install_resp_config = join(templates_dir, "install.yaml")

    resp_configs = filter(exists, [generic_install_resp_config,
                                   host_install_resp_config])

    if exists(host_install_resp):
        logging.info(f"copying host response file {host_install_resp} to {output_file}")
        shutil.copy(host_install_resp, output_file)
    elif exists(host_install_resp_template):
        logging.info(f"generating host response file {output_file}")
        config = cfg.update(*resp_configs,
                            hostname=hostname)
        render_install_resp(host_install_resp_template,
                            output_file,
                            config.to_dict())
    elif exists(generic_install_resp_template):
        logging.info(f"generating generic response file {output_file}")
        config = cfg.update(*resp_configs,
                            hostname=hostname)
        render_install_resp(generic_install_resp_template,
                            output_file,
                            config.to_dict())
    else:
        logging.error("no install response file or template")
        sys.exit(1)
