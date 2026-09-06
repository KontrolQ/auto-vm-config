from media.iso9660 import descriptors
from media.iso9660 import directories
from media.iso9660 import records
from media.iso9660 import sectors


def root_of(handle):
    volume = descriptors.primary(handle)

    if volume is None:
        return None

    return descriptors.root_record(volume)


def refuse_when_absent(record, path):
    if record is None:
        raise FileNotFoundError("%s is not on this disc" % path)


def refuse_when_a_directory(record, path):
    if records.is_directory(record):
        raise IsADirectoryError("%s is a directory, not a file" % path)


def content_of(handle, record):
    return sectors.span(
        handle, records.extent_of(record), records.data_length_of(record)
    )


def located(handle, path):
    return directories.located(handle, root_of(handle), path)


def exists(handle, path):
    return located(handle, path) is not None


def read(handle, path):
    record = located(handle, path)

    refuse_when_absent(record, path)
    refuse_when_a_directory(record, path)

    return content_of(handle, record)


def size_of(handle, path):
    record = located(handle, path)

    refuse_when_absent(record, path)

    return records.data_length_of(record)


def listed(handle, path=""):
    record = located(handle, path)

    refuse_when_absent(record, path)

    return directories.listed(handle, record)
