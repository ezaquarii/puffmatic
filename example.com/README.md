# example.com

This configuration set serves as a reference for creating your own
"domain" setups. This directory contains everything needed to create 
auto-installable media for multiple hosts within the domain.

This particular example includes configurations for two hosts and
demonstrates automatic installation both from a USB stick and over the
network.

- [hosts](hosts) directory contains configuration for individual hosts
- [site](site) contains files that will be packaged as `site77.tgz`
  set; it is accompanied by a [site.mtree](site.mtree) file for
  [mtree(8)](https://man.openbsd.org/mtree) utility
- [templates](templates) contains generic templates shared by all host
  configuration
- [config.yaml](config.yaml) is the main configuration file

> [!IMPORTANT]
> Examples demonstrate how to package ssh site keys.
> Provided site key files contain real keys, but those keys are not used
> anywhere. They just facilitate running examples on vmd(8). Do not report
> them and do not deploy them to real machines.

# [alfa](hosts/alfa)

This host example illustrates the process of creating an
autoinstallable USB image. The provided `install.conf` is tailored for
a specific host.

This image is designed to be executed using `vmd(8)`. Since `vmd(8)`
can only boot from the first image, the installer will run from `sd0`,
while the root disk must be designated as `sd1`.

The host is configured with full disk encryption, a custom
`boot.conf`, and a set of `sshd` host keys included in the
host-specific `site77-alfa.tgz`.

## Creating bootable installer image

```shell
puffmatic-usb alfa
```

The resulting image file, `install77-alfa.img`, will be located in the
output directory.

## Testing installer with `vmd(8)`

Create target disk image of at least 40G:

```shell
vmctl create -s 40G alfa.qcow2
```

```shell
vmctl start -m 2G -L -d install77-alfa.img -d alfa.qcow2 -B disk -c alfa
```

After installation, to avoid rerunning the installer again after a
reboot, power down the virtual machine and restart it using just one
disk:

```shell
vmctl start -m 2G -L -d alfa.qcow2 -B disk -c alfa
```

For guidance on configuring NAT for a virtual machine, please consult
`man 8 vmctl`.

# [bravo](hosts/bravo)

This host example demonstrates how to perform network installation
over HTTP.

This example is configured to be run using local `httpd(8)` and
`vmd(8)`.  Thereof it doesn't provide TLS configuration, but it
demonstrates application of basic auth and secret sets directory
techniques. If you want to expose install server over the network,
make sure you configure `httpd(8)` with TLS and consider using `pf` to
further limit access by IP.

## Configuring installation server

Example installation `httpd(8)` server configuration is provided in
[httpd](httpd) directory.

HTTP is configured to serve two directories: `resp` and `sets`.

Files in the `resp` directory are secured with basic authentication,
preventing 3rd parties from accessing respone files.

As the installer is unable to authenticate while accessing set
tarballs, the `sets` directory is secured by a "secret directory"
path. This paths is only known if you obtain response file.

During iterative development, it is convenient to symlink
`output/resp` and `output/sets` to your http server root directory.

## Creating installer sets and response file

```shell
puffmatic-net
```

This will place response, disklabel files in the `output/resp` and
installation sets in the `output/sets` directory.

Place the output files in `/var/www/install.example.com/sets` and
`/var/www/install.example.com/resp`. For ease of development and
testing, you can symlink those directories as `output/sets` and
`output/resp` respectvely.

## Testing installed with `vmd(8)`

Create 40GB disk image:

```shell
vmctl -s 40G bravo.qcow2
```

You can boot from ISO or boot `bsd.rd` directly:

```shell
vmctl start -m 2G -L -d bravo.qcow2 -b output/sets/bsd.rd -c bravo
```

Since allocated `tap(4)` IP address depends on virtual machine ID and
we use `100.64.1.0` network in the autoinstall response file, make
sure your virtual machine starts with ID 1 or adjust the configuration.

When prompted, choose `(A)utoinstall` and point it to a response file:

```
Welcome to the OpenBSD/amd64 7.7 installation program.
(I)nstall, (U)pgrade, (A)utoinstall or (S)hell? a
Could not determine auto mode.
Response file location? [http://100.64.1.2/install.conf] http://user:pass@100.64.1.2:8080/install-bravo.conf
(I)nstall or (U)pgrade? i
Fetching http://user:pass@100.64.1.2:8080/install-bravo.conf
Performing non-interactive install...
...
```
