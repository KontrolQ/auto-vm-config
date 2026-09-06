import os

FOLDER = "auto-vm-config"
DOWNLOADS = "downloads"

WINDOWS_VARIABLE = "LOCALAPPDATA"
POSIX_FALLBACK = os.path.join("~", ".cache")


def root():
    held = os.environ.get(WINDOWS_VARIABLE) or os.path.expanduser(POSIX_FALLBACK)

    return os.path.join(held, FOLDER, DOWNLOADS)


def prepared():
    directory = root()

    os.makedirs(directory, exist_ok=True)

    return directory


def path_for(name):
    return os.path.join(prepared(), name)
