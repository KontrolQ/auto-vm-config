import os
import shutil
import sys

SYSTEM_EMULATOR = "qemu-system-i386"
IMAGE_TOOL = "qemu-img"

RUNNING_ON_WINDOWS = sys.platform == "win32"
RUNNING_ON_MACOS = sys.platform == "darwin"

WINDOWS_EXTENSION = ".exe"

WINDOWS_DIRECTORIES = (
    "C:\\Program Files\\qemu",
    "C:\\Program Files (x86)\\qemu",
    "C:\\qemu",
)

MACOS_DIRECTORIES = (
    "/opt/homebrew/bin",
    "/usr/local/bin",
)

UNIX_DIRECTORIES = (
    "/usr/bin",
    "/usr/local/bin",
)

NOT_FOUND = None


def executable_name(stem):
    if RUNNING_ON_WINDOWS:
        return stem + WINDOWS_EXTENSION

    return stem


def known_directories():
    if RUNNING_ON_WINDOWS:
        return WINDOWS_DIRECTORIES

    if RUNNING_ON_MACOS:
        return MACOS_DIRECTORIES

    return UNIX_DIRECTORIES


def on_path(stem):
    return shutil.which(executable_name(stem))


def in_known_directories(stem):
    for directory in known_directories():
        candidate = os.path.join(directory, executable_name(stem))

        if os.path.isfile(candidate):
            return candidate

    return NOT_FOUND


def located(stem):
    return on_path(stem) or in_known_directories(stem)


def system_emulator():
    return located(SYSTEM_EMULATOR)


def image_tool():
    return located(IMAGE_TOOL)


def is_available():
    return system_emulator() is not NOT_FOUND


def searched_places():
    return ("the PATH",) + known_directories()


def refuse_when_missing():
    if is_available():
        return

    raise FileNotFoundError(
        "%s was not found; looked in %s"
        % (executable_name(SYSTEM_EMULATOR), ", ".join(searched_places()))
    )
