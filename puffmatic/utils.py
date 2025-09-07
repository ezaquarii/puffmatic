"""Various utility helpers."""
import dataclasses
import inspect
import logging
import select
import subprocess
import sys
import threading
import urllib
import yaml
from dataclasses import (dataclass, field)
from os.path import join, abspath, basename, exists


def create_logger(name=None, level=logging.INFO):
    """Create logger instance."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    console_handler = logging.StreamHandler(stream=sys.stdout)
    formatter = logging.Formatter(
        fmt="{asctime} {levelname} {name}: {message}",
        style="{",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG)
    logger.addHandler(console_handler)
    return logger


def _cmd_output_logger(logger: logging.Logger = None, stdout=None, stderr=None):
    """Redirects stdout and stderr streams to logger."""
    if logger is None:
        return
    streams = [s for s in (stdout, stderr) if s is not None]
    while streams:
        ready_to_read, _, _ = select.select(streams, [], [])
        for stream in ready_to_read:
            line = stream.readline()
            if line:
                logger.info(line.rstrip())
            else:
                streams.remove(stream)


def _format_cmd(cmd, stdout=None, stderr=None, stdin=None):
    """Format shell command, including stream redirection operators."""
    c = cmd.copy()
    if hasattr(stdin, "name") and exists(stdin.name):
        c.extend(("<", stdin.name))
    if hasattr(stdout, "name") and exists(stdout.name):
        c.extend((">", stdout.name))
    if hasattr(stderr, "name") and exists(stderr.name):
        c.extend(("2>", stderr.name))
    return " ".join(c)


def run(cmd, **kwargs):
    """Run shell command redirecting output to logger."""
    stdout = kwargs.pop("stdout", subprocess.PIPE)
    stderr = kwargs.pop("stderr", subprocess.PIPE)
    parent_logger = kwargs.pop("logger", None)
    text = kwargs.pop("text", True)
    priv = kwargs.pop("priv", False)
    check = kwargs.pop("check", False)

    full_cmd = cmd if not priv else ["doas"] + cmd
    process = subprocess.Popen(
        full_cmd,
        stdout=stdout,
        stderr=stderr,
        text=text,
        **kwargs
    )
    reader = None
    if parent_logger:
        suffix = basename(cmd[0]).replace(".", "_")
        logger = parent_logger.getChild(suffix)
        output_logger_args = {
            "logger": logger,
            "stdout": process.stdout if stdout == subprocess.PIPE else None,
            "stderr": process.stderr if stderr == subprocess.PIPE else None,
        }
        reader = threading.Thread(target=_cmd_output_logger,
                                  kwargs=output_logger_args,
                                  daemon=True)
        reader.start()
        formatted_cmd = _format_cmd(full_cmd,
                                    stdout=stdout,
                                    stderr=stderr,
                                    stdin=kwargs.get("stdin", None))
        parent_logger.debug(f"running {formatted_cmd}")
    rc = process.wait()
    if reader:
        reader.join()
    if check and rc:
        raise subprocess.CalledProcessError(rc, full_cmd)
    return rc


def parse_version(version: str | tuple) -> (int, int):
    """Parse version and return tuple of (major, minor)."""
    match version:
        case (int() as major, int() as minor):
            return (major, minor)
    v = version.split(".")
    if len(v) != 2:
        return None
    try:
        major = int(v[0])
        minor = int(v[1])
        return major, minor
    except ValueError:
        return None


def load_yaml(*files):
    """Load all yaml files and merge them together."""
    merged_data = {}
    for file in files:
        with open(file) as f:
            data = yaml.safe_load(f)
            merged_data.update(data)
    return merged_data


@dataclass
class Config():
    """
    Config provides global settings for all subcommands.

    It provides information about all locations as well
    as values for config file template rendering.
    """

    version: (int, int) = field(default=(0, 0))
    arch: str = field(default=None)
    mirror: str = field(default=None)
    install_server: str = field(default=None)
    install_server_dir: str = field(default=None)
    install_basic_auth: str = field(default=None)
    templates_dir: str = field(default=None)
    output_dir: str = field(default=None)

    hostname: str = field(default=None)
    ssh_public_key: str = field(default=None)
    root_password: str = field(default=None)
    disk_encryption_passphrase: str = field(default=None)
    disklabel: str = field(default=None)
    ipv6_address: str = field(default=None)
    ipv6_gateway: str = field(default=None)
    use_autopartitioning_template: bool = field(default=False)

    def __post_init__(self):
        """Convert values to native types."""
        self.version = parse_version(self.version)
        if self.templates_dir:
            self.templates_dir = abspath(self.templates_dir)
        if self.output_dir:
            self.output_dir = abspath(self.output_dir)

    @property
    def version_full(self):
        """Format version."""
        return f"{self.version[0]}.{self.version[1]}"

    @property
    def version_short(self):
        """Format version in short format, without dot."""
        return f"{self.version[0]}{self.version[1]}"

    @property
    def sets_output_dir(self):
        """Directory where output site tests are written."""
        return join(self.output_dir, "sets")

    @property
    def resp_output_dir(self):
        """Directory where output response files are written."""
        return join(self.output_dir, "resp")

    @property
    def img_output_dir(self):
        """Directory where output installer image file is written."""
        return join(self.output_dir, "img")

    @property
    def tmp_dir(self):
        """Temporary directory."""
        return join(self.output_dir, "tmp")

    @property
    def resp_server_url(self):
        """Formatted server url where response file can be downloaded."""
        u = urllib.parse.urlparse(self.install_server)
        if self.install_basic_auth:
            return f"{u.scheme}://{self.install_basic_auth}@{u.netloc}"
        else:
            return f"{u.scheme}://{u.netloc}"

    @property
    def disklabel_server_url(self):
        """Formatted server url where disklabel file can be downloaded."""
        return self.resp_server_url

    @property
    def install_server_url(self):
        """Formatted server url where installation sets are hosted."""
        return self.install_server

    @classmethod
    def load(cls, *files: str):
        """Load environment configuration."""
        return Config().update(*files)

    def update(self, *files, **kwargs):
        """Upload environment from set of files."""
        d = load_yaml(*files)
        d.update(kwargs)
        return dataclasses.replace(self, **d)

    def to_dict(self):
        """Convert config objects to dictionary."""
        d = dataclasses.asdict(self)
        props = inspect.getmembers(self.__class__,
                                   lambda p: isinstance(p, property))
        for name, attr in props:
            d[name] = getattr(self, name)
        return d
