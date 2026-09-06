import os

from catalogue import checksums, downloads, queries, storage
from definitions import updates

SIZE = "sizeBytes"
CHECKSUM = "checksum"
ALGORITHM = "checksumAlgorithm"
ADDRESS = "downloadUrl"

UNKNOWN_SIZE = 0

MISMATCH = "%s does not match the checksum the catalogue publishes"
NO_ADDRESS = "%s cannot be downloaded; the catalogue publishes no address for it"
UNKNOWN_ALGORITHM = (
    "%s publishes a %s checksum, which this tool cannot compute; it will not be "
    "installed unverified"
)
TAKEN_AWAY = (
    "%s downloaded and matched its checksum, but this machine will no longer read it; "
    "antivirus quarantine is the usual cause, and %s is the folder to allow"
)


def reference_of(entry):
    return updates.catalogue_of(entry)


def is_catalogued(entry):
    return reference_of(entry) is not None


def catalogued(entries):
    return [entry for entry in entries if is_catalogued(entry)]


def uncatalogued(entries):
    return [entry for entry in entries if not is_catalogued(entry)]


def record_for(entry):
    return queries.looked_up(reference_of(entry))


def size_of(record):
    return record.get(SIZE) or UNKNOWN_SIZE


def address_of(record):
    return record.get(ADDRESS)


def has_checksum(record):
    return bool(record.get(CHECKSUM))


def verifiable(record):
    return has_checksum(record) and checksums.supported(record.get(ALGORITHM))


def refuse_unusable_checksum(entry, record):
    if verifiable(record) or not has_checksum(record):
        return

    raise ValueError(
        UNKNOWN_ALGORITHM
        % (queries.described(reference_of(entry)), record.get(ALGORITHM) or "nameless")
    )


def cached_name(entry):
    return f"{reference_of(entry)[queries.ITEM]}-{updates.file_of(entry)}"


def sized_right(path, record):
    return not size_of(record) or os.path.getsize(path) == size_of(record)


def readable(path):
    try:
        with open(path, "rb") as reading:
            reading.read(1)
    except OSError:
        return False

    return True


def sound(path, record):
    if not sized_right(path, record):
        return False

    if not verifiable(record):
        return True

    return checksums.matches(path, record[ALGORITHM], record[CHECKSUM])


def cached(entry, record):
    refuse_unusable_checksum(entry, record)

    path = storage.path_for(cached_name(entry))

    if not os.path.isfile(path) or not readable(path):
        return None

    return path if sound(path, record) else None


def discard(path):
    try:
        os.remove(path)
    except OSError:
        return


def refuse_mismatch(entry, digest, record, path):
    if digest is None or checksums.agree(digest.hexdigest(), record[CHECKSUM]):
        return

    discard(path)

    raise ValueError(MISMATCH % queries.described(reference_of(entry)))


def refuse_unreadable(entry, path):
    if readable(path):
        return

    discard(path)

    raise LookupError(TAKEN_AWAY % (queries.described(reference_of(entry)), storage.root()))


def fetch(entry, record, progressed):
    refuse_unusable_checksum(entry, record)

    address = address_of(record)

    if not address:
        raise LookupError(NO_ADDRESS % queries.described(reference_of(entry)))

    digest = checksums.digest_for(record[ALGORITHM]) if verifiable(record) else None
    path = downloads.to_file(address, storage.path_for(cached_name(entry)), progressed, digest)

    refuse_mismatch(entry, digest, record, path)
    refuse_unreadable(entry, path)

    return path
