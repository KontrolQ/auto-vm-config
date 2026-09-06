from filesystems.fat12 import files, layout

LOADER = "JO.SYS"

SIGNATURE = b"CD-ROM Startup Menu"


def is_present(image):
    return SIGNATURE in bytes(image)


def carries_the_loader(image, parameters):
    return files.exists(image, parameters, LOADER)


def without(image):
    held = bytearray(image)

    if not is_present(held):
        return bytes(held)

    parameters = layout.parameters(held)

    if not carries_the_loader(held, parameters):
        return bytes(held)

    files.remove(held, parameters, LOADER)

    return bytes(held)
