import os
import shutil
import sys

SAMBA_BINARY = "smbd"

UNSUPPORTED_PLATFORMS = ("win32",)

GUEST_ADDRESS = "10.0.2.4"

NO_COMPLAINT = None


def platform_allows_sharing():
    return sys.platform not in UNSUPPORTED_PLATFORMS


def samba_is_present():
    return shutil.which(SAMBA_BINARY) is not None


def is_supported():
    return platform_allows_sharing() and samba_is_present()


def complaint():
    if not platform_allows_sharing():
        return "shared folders need a Samba daemon, which this host has none of"

    if not samba_is_present():
        return f"{SAMBA_BINARY} is not on the PATH, so no folder can be shared"

    return NO_COMPLAINT


def is_wanted(path):
    return bool(path)


def refuse_missing_folder(path):
    if not os.path.isdir(path):
        raise NotADirectoryError(f"{path} is not a folder on this machine")


def netdev_options(path):
    if not is_wanted(path) or not is_supported():
        return []

    refuse_missing_folder(path)

    return [f"smb={os.path.abspath(path)}"]


def guest_address():
    return GUEST_ADDRESS
