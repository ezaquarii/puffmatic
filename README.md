# Puffmatic - OpenBSD Autoinstall Generator

This script facilitates the preparation of files for unattended
OpenBSD installation. Refer to
[autoinstall(8)](https://man.openbsd.org/autoinstall) for more
details.

The provided examples allow you to create auto-installable sets for
USB and network installations. This tutorial demonstrates how to test
these sets on a [vmd(8)](https://man.openbsd.org/vmd) virtual machine.

## Installation

### Installing from PyPI

Puffmatic is released to PyPI, so you can install it using `pip`:

```shell
python3 -m venv venv
. venv/bin/activate
pip install puffmatic
```

### Running from source directory

This script runs on OpenBSD and requires Python 3. All dependencies
are in base system or are installed by `pip`.  Checkout source
directory from git to boostrap it:

```shell
make bootstrap
```

It will create `venv` and install handful of dependencies to run, test
and develop `puffmatic`.

If you are using `envrc`, provided `.envrc` will ensure `venv` is activated,
and `PYTHONPATH` and `PATH` are updated for seamless use.

If you don't run `envrc`, you can source the shell environment
manually to the same effect:

```shell
. .envrc
```

Test with:

```shell
python3 -m puffmatic help
```

Last but not least, you must grant access to some shell utilities in
priviledged mode. Put this in your `/etc/doas.conf`:

```
permit nopass user cmd mount
permit nopass user cmd umount
permit nopass user cmd vnconfig
permit nopass user cmd install
```

If you are concerned about elevated priviledges, create a dedicated
user account.

## example.com

Once installed, you should explore the example. Go stright to
[example.com README.md](example.com/README.md), where you will find
further documentation and a tutorial runnable using `vmd(8)`.

The example is "self documenting" in the sense that all elements are
covered by adjacent `README.md` files scattered around.

Enjoy!
