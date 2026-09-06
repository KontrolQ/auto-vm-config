import os
import re

from definitions import loading

PLACEHOLDER = re.compile("{{([a-z0-9_]+)}}")

ENCODING = "ascii"
UNSUPPORTED_CHARACTERS = "replace"

LINE_ENDING = "\r\n"


def path_of(identifier, name):
    return os.path.join(loading.assets_directory(identifier), name)


def exists(identifier, name):
    return os.path.isfile(path_of(identifier, name))


def available(identifier):
    directory = loading.assets_directory(identifier)

    if not os.path.isdir(directory):
        return []

    return sorted(
        name for name in os.listdir(directory) if os.path.isfile(os.path.join(directory, name))
    )


def refuse_when_missing(identifier, name):
    if exists(identifier, name):
        return

    raise FileNotFoundError(
        "{} has no asset named {}; it holds {}".format(
            identifier, name, ", ".join(available(identifier)) or "none"
        )
    )


def read_bytes(identifier, name):
    refuse_when_missing(identifier, name)

    with open(path_of(identifier, name), "rb") as handle:
        return handle.read()


def as_dos_text(text):
    return LINE_ENDING.join(text.splitlines()) + LINE_ENDING


def read_text(identifier, name):
    return as_dos_text(read_bytes(identifier, name).decode(ENCODING, UNSUPPORTED_CHARACTERS))


def placeholders_in(text):
    return sorted(set(PLACEHOLDER.findall(text)))


def refuse_unfilled(text, values):
    missing = [name for name in placeholders_in(text) if name not in values]

    if missing:
        raise KeyError("nothing was given for {}".format(", ".join(missing)))


def filled(text, values):
    refuse_unfilled(text, values)

    return PLACEHOLDER.sub(lambda found: str(values[found.group(1)]), text)


def prepared(identifier, name, values):
    return filled(read_text(identifier, name), values).encode(ENCODING, UNSUPPORTED_CHARACTERS)
