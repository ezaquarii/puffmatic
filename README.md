# Puffmatic - OpenBSD Autoinstall Generator

This script streamlines the preparation of files for unattended
OpenBSD installations using USB thumb drives and HTTP.

It modifies the USB installer image with
[autoinstall(8)](https://man.openbsd.org/autoinstall) response files
and site sets.

Additionally, the script can create a collection of response files,
disk label files, and site set archives, which are suitable for
serving through [httpd(8)](https://man.openbsd.org/httpd).

This approach is particularly beneficial for faster provisioning on
budget VPS systems where TFTP boot is not an option. Simply boot the
installer from the vendor-provided image and direct it to the
self-hosted response file. Installation assets can be secured using
basic authentication (don't forget about TLS!).

Provided [example.com](example.com) domain configuration can be tested
using [vmd(8)](https://man.openbsd.org/vmd) and
[httpd(8)](https://man.openbsd.org/httpd) locally.

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
