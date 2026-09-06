import os
import re

from cli_widgets.rendering import frames, styling
from cli_widgets.widgets import browser

from install import validation
from media.eltorito import images
from media.iso9660 import descriptors, files

MARKERS = "markers"

PRODUCT_KEY = "product_key"
PATTERN = "pattern"
REQUIRED = "required"

DISC_SUFFIXES = (".iso", ".img", ".bin", ".cue")
FLOPPY_SUFFIXES = (".img", ".ima", ".flp", ".vfd")

NOTHING = None


def complain(text):
    frames.write("  " + styling.danger(text) + "\n")


def chosen_file(question, suffixes, validator, start):
    while True:
        path = browser.ask_file(question, start, suffixes)
        complaint = validator(path)

        if complaint is validation.ACCEPTED:
            return path

        complain(complaint)
        start = os.path.dirname(path) or start


def is_a_volume(path):
    with open(path, "rb") as handle:
        return descriptors.holds_a_volume(handle)


def holds_the_markers(path, guest):
    with open(path, "rb") as handle:
        return all(files.exists(handle, marker) for marker in guest["disc"].get(MARKERS, []))


def disc_validator(guest):
    def check(value):
        if not os.path.isfile(value):
            return "that is not a file"

        if not is_a_volume(value):
            return "that file is not a disc image"

        if not holds_the_markers(value, guest):
            return "that disc does not carry this guest's installation files"

        return validation.ACCEPTED

    return check


def ask_disc(guest, start="."):
    return chosen_file("Installation disc", DISC_SUFFIXES, disc_validator(guest), start)


def volume_of(path):
    with open(path, "rb") as handle:
        return descriptors.volume_identifier(descriptors.primary(handle))


def key_settings(guest):
    return guest.get(PRODUCT_KEY, {})


def wants_a_product_key(guest):
    return key_settings(guest).get(REQUIRED, False)


def read_key(path):
    with open(path, encoding="ascii", errors="replace") as handle:
        return handle.read().strip()


def key_file_validator(guest):
    pattern = key_settings(guest).get(PATTERN)

    def check(value):
        if not os.path.isfile(value):
            return "that is not a file"

        if pattern and not re.match(pattern, read_key(value)):
            return "that file does not hold a key in the expected form"

        return validation.ACCEPTED

    return check


def ask_product_key(guest, start="."):
    if not wants_a_product_key(guest):
        return ""

    return read_key(
        chosen_file("Product key file", browser.ANY_FILE, key_file_validator(guest), start)
    )


def disc_carries_a_floppy(path):
    with open(path, "rb") as handle:
        return images.carries_a_boot_floppy(handle)


def floppy_validator():
    def check(value):
        if not os.path.isfile(value):
            return "that is not a file"

        return validation.ACCEPTED

    return check


def ask_floppy(start="."):
    return chosen_file("Boot floppy image", FLOPPY_SUFFIXES, floppy_validator(), start)


def floppy_for(disc_path, guest, start="."):
    if guest["boot"].get("prefer") == "disc" and disc_carries_a_floppy(disc_path):
        return NOTHING

    frames.write("  " + styling.warning("this disc carries no boot floppy") + "\n")

    return ask_floppy(start)
