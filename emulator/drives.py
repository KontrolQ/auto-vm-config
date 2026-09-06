SYSTEM_DISK = "system_disk"
DATA_DISK = "data_disk"
DISC = "disc"
FLOPPY = "floppy"

RAW = "raw"

IDE = "ide"
FLOPPY_INTERFACE = "floppy"

DISK_MEDIA = "disk"
DISC_MEDIA = "cdrom"

FROM_FLOPPY = "a"
FROM_DISK = "c"
FROM_DISC = "d"

BOOT_LETTERS = {
    FLOPPY: FROM_FLOPPY,
    SYSTEM_DISK: FROM_DISK,
    DISC: FROM_DISC,
}

AFTER_FIRST_BOOT = {
    FLOPPY: FROM_DISK,
    DISC: FROM_DISK,
}


def drive_options(path, interface, index, media):
    return f"file={path},format={RAW},if={interface},index={index},media={media}"


def disk_arguments(path, index):
    return ["-drive", drive_options(path, IDE, index, DISK_MEDIA)]


def disc_arguments(path, index):
    return ["-drive", drive_options(path, IDE, index, DISC_MEDIA)]


def floppy_arguments(path):
    return ["-drive", drive_options(path, FLOPPY_INTERFACE, 0, DISK_MEDIA)]


def attached(paths):
    arguments = []

    if paths.get(SYSTEM_DISK):
        arguments += disk_arguments(paths[SYSTEM_DISK], 0)

    if paths.get(DATA_DISK):
        arguments += disk_arguments(paths[DATA_DISK], 1)

    if paths.get(DISC):
        arguments += disc_arguments(paths[DISC], 2)

    if paths.get(FLOPPY):
        arguments += floppy_arguments(paths[FLOPPY])

    return arguments


def refuse_unknown_boot_source(source):
    if source not in BOOT_LETTERS:
        raise ValueError(
            "{} is not a boot source; use one of {}".format(source, ", ".join(sorted(BOOT_LETTERS)))
        )


def boot_arguments(source):
    refuse_unknown_boot_source(source)

    afterwards = AFTER_FIRST_BOOT.get(source)

    if afterwards is None:
        return ["-boot", f"order={BOOT_LETTERS[source]}"]

    return ["-boot", f"once={BOOT_LETTERS[source]},order={afterwards}"]
