LENGTH = 11
PADDING = " "
ABSENT = "NO NAME"

FORBIDDEN_CHARACTERS = '*?/\\|,;:+=<>[]"'
REPLACEMENT_CHARACTER = "_"


def acceptable(character):
    if character in FORBIDDEN_CHARACTERS:
        return REPLACEMENT_CHARACTER

    if ord(character) < 0x20:
        return REPLACEMENT_CHARACTER

    return character


def cleaned(volume_label):
    return "".join(acceptable(character) for character in volume_label.upper())


def padded(volume_label):
    return cleaned(volume_label or ABSENT)[:LENGTH].ljust(LENGTH, PADDING)


def encoded(volume_label):
    return padded(volume_label).encode("ascii")


def decoded(raw):
    return raw[:LENGTH].decode("ascii", "replace").rstrip(PADDING)
