import os
import urllib.request

from catalogue import addresses

TIMEOUT = 60
CHUNK = 1024 * 64

PARTIAL_SUFFIX = ".part"


def opened(address):
    request = urllib.request.Request(address, headers=addresses.headers())

    return urllib.request.urlopen(request, timeout=TIMEOUT)


def drained(answer, writing, progressed, digest):
    while True:
        block = answer.read(CHUNK)

        if not block:
            return

        writing.write(block)

        if digest is not None:
            digest.update(block)

        progressed(len(block))


def to_file(address, path, progressed, digest=None):
    partial = path + PARTIAL_SUFFIX

    try:
        with opened(addresses.absolute(address)) as answer:
            with open(partial, "wb") as writing:
                drained(answer, writing, progressed, digest)
    except BaseException:
        if os.path.isfile(partial):
            os.remove(partial)

        raise

    os.replace(partial, path)

    return path
