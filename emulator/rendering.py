import subprocess
import sys

RUNNING_ON_WINDOWS = sys.platform == "win32"

SAFE_CHARACTERS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@%_+=:,./-")

FLAG_PREFIX = "-"


def needs_quoting(argument):
    return not argument or not set(argument) <= SAFE_CHARACTERS


def posix_quoted(argument):
    if not needs_quoting(argument):
        return argument

    return "'" + argument.replace("'", "'\"'\"'") + "'"


def windows_quoted(argument):
    return subprocess.list2cmdline([argument])


def quoted(argument):
    if RUNNING_ON_WINDOWS:
        return windows_quoted(argument)

    return posix_quoted(argument)


def as_one_line(command):
    return " ".join(quoted(argument) for argument in command)


def is_a_flag(argument):
    return argument.startswith(FLAG_PREFIX)


def grouped(command):
    groups = []

    for argument in command:
        if is_a_flag(argument) or not groups:
            groups.append([argument])
        else:
            groups[-1].append(argument)

    return groups


def as_grouped_lines(command):
    return [" ".join(quoted(part) for part in group) for group in grouped(command)]
