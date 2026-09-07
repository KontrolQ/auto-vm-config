# auto-vm-config

Builds a QEMU virtual machine and installs its guest without you sitting through the
installer. You answer a handful of questions; it writes the disks, prepares the boot
floppy, generates the answer file the installer reads, and starts the machine.

It installs the operating system and nothing else. Anything you want on top of it goes
on afterwards, by hand.

## Running it

```sh
uv run configure.py
```

It asks what to install, where to put the machine, which disc to install from, and for
a file holding the product key. Then the hardware — processor, memory, disk sizes,
display, sound, network, pointer — and the details the installer would otherwise stop
and ask for, such as the machine's name and time zone. It takes no command-line
options.

## What it writes

A folder named after the machine, holding the disk images, the boot floppy, and one
script — `run.cmd` on Windows, `run.sh` on everything else:

```sh
run.sh install   # installs the guest, once
run.sh           # starts the machine, every time after that
```

The script names the emulator and the images by absolute path, so it belongs to the
machine that built it. Build again on another host rather than carrying it across.

## Defining a guest

Everything about a guest is data, under `guests/<name>/`:

| File | What it holds |
| --- | --- |
| `guest.toml` | how it boots, how setup is run, and the answer file's fixed sections |
| `hardware.toml` | the hardware questions and the values each answer maps to |
| `questions.toml` | what the installer needs to be told, and where each answer is written |
| `timezones.toml` | the time zones the guest recognises, with their offsets |
| `assets/` | files copied into the machine, such as the startup batch file |

Adding a guest means adding a folder, so long as it installs the way this one does:
boot a floppy, run setup against an answer file, then run whatever was staged.

## What it needs

QEMU on the PATH or in the usual place for the platform, an installation disc, and a
product key if the guest wants one. Everything else — partitioning the disk, formatting
it, writing FAT12 and FAT32, reading the disc and its boot image — is done here rather
than by shelling out.
