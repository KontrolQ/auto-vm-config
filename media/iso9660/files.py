from media.iso9660 import descriptors, directories, records, sectors


def root_of(handle):
    volume = descriptors.primary(handle)

    if volume is None:
        return None

    return descriptors.root_record(volume)


def refuse_when_absent(record, path):
    if record is None:
        raise FileNotFoundError(f"{path} is not on this disc")


def refuse_when_a_directory(record, path):
    if records.is_directory(record):
        raise IsADirectoryError(f"{path} is a directory, not a file")


def content_of(handle, record):
    return sectors.span(handle, records.extent_of(record), records.data_length_of(record))


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
