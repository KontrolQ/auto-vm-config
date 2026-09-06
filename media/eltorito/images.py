from media.eltorito import catalogue
from media.iso9660 import descriptors, sectors

SPECIFICATION = "EL TORITO SPECIFICATION"


def announces_el_torito(record):
    return descriptors.boot_system_identifier(record).startswith(SPECIFICATION)


def catalogue_of(handle):
    record = descriptors.boot_record(handle)

    if record is None or not announces_el_torito(record):
        return None

    raw = sectors.sector(handle, descriptors.boot_catalogue_block(record))

    if not catalogue.is_valid(raw):
        return None

    return raw


def entry_on(handle):
    raw = catalogue_of(handle)

    if raw is None:
        return None

    return catalogue.initial_entry(raw)


def details_of(handle):
    entry = entry_on(handle)

    if entry is None:
        return None

    return catalogue.read(catalogue_of(handle))


def carries_a_boot_image(handle):
    entry = entry_on(handle)

    return entry is not None and catalogue.is_bootable(entry)


def carries_a_boot_floppy(handle):
    entry = entry_on(handle)

    return entry is not None and catalogue.is_bootable(entry) and catalogue.is_a_floppy(entry)


def refuse_when_absent(entry):
    if entry is None:
        raise ValueError("this disc carries no boot image")


def extracted(handle):
    entry = entry_on(handle)

    refuse_when_absent(entry)

    return sectors.span(handle, catalogue.load_block_of(entry), catalogue.size_of(entry))
