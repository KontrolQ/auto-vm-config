STEM_LENGTH = 8
EXTENSION_LENGTH = 3
PACKED_LENGTH = STEM_LENGTH + EXTENSION_LENGTH

SEPARATOR = "."
PADDING = " "

FORBIDDEN_CHARACTERS = '"*+,/:;<=>?[\\]|'
REPLACEMENT_CHARACTER = "_"


def acceptable(character):
    if character in FORBIDDEN_CHARACTERS:
        return REPLACEMENT_CHARACTER

    if ord(character) < 0x20:
        return REPLACEMENT_CHARACTER

    return character


def cleaned(text):
    return "".join(acceptable(character) for character in text.upper())


def split_into_stem_and_extension(name):
    if SEPARATOR not in name:
        return name, ""

    stem, _, extension = name.rpartition(SEPARATOR)

    return stem, extension


def fitted(text, length):
    return cleaned(text)[:length].ljust(length, PADDING)


def packed(name):
    stem, extension = split_into_stem_and_extension(name)

    return (fitted(stem, STEM_LENGTH) + fitted(extension, EXTENSION_LENGTH)).encode(
        "ascii"
    )


def unpacked(raw):
    stem = raw[:STEM_LENGTH].decode("ascii", "replace").rstrip(PADDING)
    extension = raw[STEM_LENGTH:PACKED_LENGTH].decode("ascii", "replace").rstrip(PADDING)

    if not extension:
        return stem

    return stem + SEPARATOR + extension
