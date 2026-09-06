import os

from definitions import assets, updates
from filesystems.naming import shortnames

ARGUMENTS = "arguments"
NAME = "name"

NOTHING_FOUND = None
NOTHING_PROVIDED = {}

LINE_ENDING = "\r\n"


def wanted_file(entry):
    return updates.file_of(entry)


def stored_name(wanted):
    return shortnames.unpacked(shortnames.packed(os.path.basename(wanted)))


def matches(name, wanted):
    return name.upper() == os.path.basename(wanted).upper()


def provided_for(entry, provided):
    held = provided.get(updates.identifier_of(entry))

    if held and os.path.isfile(held):
        return held

    return NOTHING_FOUND


def located(entry, directory, provided=NOTHING_PROVIDED):
    held = provided_for(entry, provided)

    if held is not NOTHING_FOUND:
        return held

    wanted = wanted_file(entry)

    if not wanted or not directory or not os.path.isdir(directory):
        return NOTHING_FOUND

    for name in sorted(os.listdir(directory)):
        if matches(name, wanted):
            return os.path.join(directory, name)

    return NOTHING_FOUND


def contents_of(path):
    with open(path, "rb") as reading:
        return reading.read()


def surveyed(entries, directory, provided=NOTHING_PROVIDED):
    return [{"entry": entry, "found": located(entry, directory, provided)} for entry in entries]


def present(survey):
    return [held for held in survey if held["found"] is not NOTHING_FOUND]


def absent(survey):
    return [held for held in survey if held["found"] is NOTHING_FOUND]


def staged_files(survey, target_directory):
    return {
        target_directory + "/" + stored_name(wanted_file(held["entry"])): contents_of(held["found"])
        for held in present(survey)
    }


def step_values(entry, guest_directory):
    return {
        "name": entry[NAME],
        "directory": guest_directory,
        "file": stored_name(wanted_file(entry)),
        "arguments": entry.get(ARGUMENTS, ""),
    }


def steps_for(identifier, survey, guest_directory, step_asset):
    return LINE_ENDING.join(
        assets.filled(
            assets.read_text(identifier, step_asset),
            step_values(held["entry"], guest_directory),
        ).strip()
        for held in present(survey)
    )


def runner_for(identifier, survey, guest_directory, runner_asset, step_asset):
    return assets.prepared(
        identifier,
        runner_asset,
        {"steps": steps_for(identifier, survey, guest_directory, step_asset)},
    )


def ordered_entries(catalogue, chosen):
    return updates.sequence_for(catalogue, chosen)
