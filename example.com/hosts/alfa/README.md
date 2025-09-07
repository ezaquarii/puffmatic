# alfa.example.com

This host configuration is suitable for installation using a USB thumb
drive.

## site and site.mtree

This directory is packaged as `site77-alfa.tgz`. The files within
`site` are included with attributes defined in `site.mtree`.

## boot.conf

Custom `boot.conf` will be placed in patched `install77.img`. This is
useful if we're installing on a host without VGA console, so we don't
have to switch console manually in boot prompt.

## disklabel

This file will be placed in the ramdisk root and used to partition the
drive. Please consult the
[disklabel(8)](https://man.openbsd.org/disklabel), specifically the
"AUTOMATIC DISK ALLOCATION" section.

## install.conf

This is a response file that will be embedded into the ramdisk root
verbatim, without any template processing.
