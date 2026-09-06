import os
import stat
import subprocess
import sys

from emulator import rendering

RUNNING_ON_WINDOWS = sys.platform == "win32"

ASSETS_DIRECTORY = "assets"

WINDOWS_SUFFIX = ".cmd"
POSIX_SUFFIX = ".sh"

WINDOWS_LINE_ENDING = "\r\n"
POSIX_LINE_ENDING = "\n"

TEMPLATE_STEM = "run"
RUN_SCRIPT = "run"

INSTALL_ARGUMENT = "install"

RUN_PLACEHOLDER = "{{run_command}}"
INSTALL_PLACEHOLDER = "{{install_command}}"

EXECUTABLE_BITS = stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH

ENCODING = "ascii"


def suffix():
    if RUNNING_ON_WINDOWS:
        return WINDOWS_SUFFIX

    return POSIX_SUFFIX


def line_ending():
    if RUNNING_ON_WINDOWS:
        return WINDOWS_LINE_ENDING

    return POSIX_LINE_ENDING


def template_path():
    return os.path.join(os.path.dirname(__file__), ASSETS_DIRECTORY, TEMPLATE_STEM + suffix())


def template():
    with open(template_path(), encoding=ENCODING) as handle:
        return handle.read()


def script_name(stem):
    return stem + suffix()


def made_runnable(path):
    if RUNNING_ON_WINDOWS:
        return

    os.chmod(path, os.stat(path).st_mode | EXECUTABLE_BITS)


def filled(install_command, run_command):
    return (
        template()
        .replace(INSTALL_PLACEHOLDER, rendering.as_one_line(install_command))
        .replace(RUN_PLACEHOLDER, rendering.as_one_line(run_command))
    )


def written(directory, install_command, run_command):
    path = os.path.join(directory, script_name(RUN_SCRIPT))

    with open(path, "w", encoding=ENCODING, newline=line_ending()) as handle:
        handle.write(filled(install_command, run_command))

    made_runnable(path)

    return path


def scripts_for(directory, install_command, run_command):
    return {RUN_SCRIPT: written(directory, install_command, run_command)}


def start(command, directory):
    return subprocess.Popen(command, cwd=directory)
