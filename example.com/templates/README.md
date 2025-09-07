# templates

Templates are used by default when host doesn't supply its files.

## disklabel

Default `disklabel` file. This file will only be used if the host does
not provide their own.

## install.conf.j2

Default response file template. This template will only be used when
the host does not provide their own.

## install.yaml

This document contains standard host configuration settings. It will
be merged with `config.yaml` and the host-specific `install.yaml`.

