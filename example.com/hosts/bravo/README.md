# bravo.example.com

This is host configuration suitable for installation over network.

## site and site.mtree

This directory is packaged as `site77-bravo.tgz`. The files within
`site` are packaged with the attributes specified in `site.mtree`.

## disklabel

This file will be located in the root of the ramdisk and used to
partition the drive. For more information, refer to the "AUTOMATIC
DISK ALLOCATION" section of
[disklabel(8)](https://man.openbsd.org/disklabel).

The disklabel will be placed in `output/resp`, alongside the response
file, to be served over HTTP.

## install.yaml

Host configuration file. It will be merged with `config.yaml` and used
to render `install.conf` using Jinja2.

## install.conf.j2

This is a response template file that will be processed with Jinja2,
using values from `install.conf` and `config.yaml`. The resulting
response file will be placed in `output/resp` to be served over HTTP.
