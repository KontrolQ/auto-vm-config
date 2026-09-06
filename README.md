# auto-vm-config

Builds a QEMU virtual machine and installs an old operating system into it without you
sitting through the installer. You answer a handful of questions; it writes the disks,
prepares the boot floppy, generates the installer's answer file, and starts the machine.

Windows 98 Second Edition is the guest it ships with.

## Running it

```sh
uv run configure.py
```

It asks what to install, where to put the machine, which disc to install from, and for
a file holding the product key. Then the hardware — processor, memory, disk sizes,
display, sound, network, pointer — and the details the installer would otherwise stop
and ask for, such as the machine's name and time zone. Nothing is passed on the command
line; there are no options.

## What it writes

A folder named after the machine, holding the disk images, the boot floppy, and one
script — `run.cmd` on Windows, `run.sh` on everything else:

```sh
run.sh install   # installs the guest, once
run.sh           # starts the machine, every time after that
```

The script names the emulator and the images by absolute path, so it belongs to the
machine that built it. Build again on another host rather than carrying it across.

## Updates

A guest can list updates to install after the operating system is up. Each one names a
file in a software catalogue; at build time it is fetched, checked against the checksum
the catalogue publishes, and kept in a cache so a later build does not download it
again. The files are copied onto the system disk and run when the guest first starts.

An update whose checksum cannot be computed is refused rather than installed unverified.

## Defining a guest

Everything about a guest is data, under `guests/<name>/`:

| File | What it holds |
| --- | --- |
| `guest.toml` | how it boots, how setup is run, and the answer file's fixed sections |
| `hardware.toml` | the hardware questions and the values each answer maps to |
| `questions.toml` | what the installer needs to be told, and where each answer is written |
| `updates.toml` | the updates offered, in the order they install |
| `timezones.toml` | the time zones the guest recognises, with their offsets |
| `assets/` | files copied into the machine, such as the startup batch file |

Adding a guest means adding a folder. No code changes if it installs the same way.

## What it needs

QEMU on the PATH or in the usual place for the platform, an installation disc, and a
product key if the guest wants one. Everything else — partitioning the disk, formatting
it, writing FAT12 and FAT32, reading the disc and its boot image — is done here rather
than by shelling out.
