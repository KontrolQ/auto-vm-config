import os
import sys

from cli_widgets.rendering import frames, styling
from cli_widgets.widgets import browser, choice, confirm, progress, prompting, summary

import clock
from definitions import loading, zones
from emulator import commands, devices, drives, launcher, sharing
from install import answerfile, asking, building, media

GUEST_DOCUMENT = "guest"
HARDWARE_DOCUMENT = "hardware"
QUESTIONS_DOCUMENT = "questions"
ZONES_DOCUMENT = "timezones"

TIME_ZONE_QUESTION = "time_zone"

GROUPS = "group"
QUESTIONS = "question"

SHARED_FOLDER = "shared_folder"

NAME_PATTERN = "^[A-Za-z0-9][A-Za-z0-9._-]{0,31}$"
NAME_LIMIT = 32


TITLE = "Ready to build"

ABANDONED = "Nothing was written."
INTERRUPTED = "Stopped. Nothing was written."


def announce(text):
    frames.write(text + "\n")


def heading(text):
    prompting.add(["", styling.bold(styling.underlined(text))])


def remark(text):
    prompting.add(["  " + styling.muted(text)])


def header_for(guest, machine_name=""):
    return [frames.bar(guest["guest"]["name"], machine_name), ""]


def guest_options(available):
    options = []

    for identifier in available:
        guest = loading.document(loading.load(identifier), GUEST_DOCUMENT)["guest"]

        options.append(
            {
                "label": guest["name"],
                "note": guest.get("family", ""),
                asking.VALUE: identifier,
            }
        )

    return options


def choose_guest():
    available = loading.available()

    if not available:
        raise FileNotFoundError("no guests are defined")

    return choice.ask("What should be installed", guest_options(available))[asking.VALUE]


def ask_machine_name(identifier):
    return asking.ask_entry(
        {
            "question": "Name for this machine",
            "default": identifier,
            "placeholder": "used for the folder it is created in",
            "required": True,
            "pattern": NAME_PATTERN,
            "limit": NAME_LIMIT,
        }
    )


def ask_location():
    return browser.ask_folder("Where should it be created", os.getcwd())


def holds_anything(directory):
    return os.path.isdir(directory) and bool(os.listdir(directory))


def may_overwrite(directory):
    if not holds_anything(directory):
        return True

    announce("")
    announce(styling.warning(f"  {directory} already holds files"))

    return confirm.ask("Overwrite what is there", False)


def hardware_groups(definition):
    declared = loading.document(definition, HARDWARE_DOCUMENT).get(GROUPS, [])

    if sharing.is_supported():
        return declared

    return [group for group in declared if group[asking.KEY] != SHARED_FOLDER]


def offered_zones(definition):
    return loading.document(definition, ZONES_DOCUMENT)


def with_zones(declaration, definition):
    if declaration[asking.KEY] != TIME_ZONE_QUESTION:
        return declaration

    held = offered_zones(definition)

    return dict(
        declaration,
        options=zones.options_of(held),
        default=zones.for_offset(held, clock.utc_offset_minutes()),
    )


def guest_questions(definition):
    declared = loading.document(definition, QUESTIONS_DOCUMENT).get(QUESTIONS, [])

    return [with_zones(declaration, definition) for declaration in declared]


def report_sharing():
    if sharing.is_supported():
        return

    remark(sharing.complaint())
    remark("files can be placed on the second disk instead")


def summary_rows(identifier, name, directory, disc_path, configuration, answers):
    rows = [
        ("Guest", identifier),
        ("Machine", name),
        ("Folder", directory),
        ("Disc", disc_path),
    ]

    rows += [(key.replace("_", " ").capitalize(), value) for key, value in configuration.items()]
    rows += [(key.replace("_", " ").capitalize(), value or "-") for key, value in answers.items()]
    rows += [("Clock", f"host, {clock.described_offset()}")]

    return rows


def report_built(built):
    announce("")
    announce(styling.bold(styling.underlined("Written")))
    announce("")

    for name, path in built.items():
        readable = name.replace("_", " ")

        announce(f"  {readable:<14} {path}")


def running_paths(built):
    return {
        name: path for name, path in built.items() if name in (drives.SYSTEM_DISK, drives.DATA_DISK)
    }


def report_scripts(scripts, configuration):
    announce("")
    announce(styling.bold(styling.underlined("To launch")))
    announce("")
    announce(f"  {scripts[launcher.RUN_SCRIPT]} {launcher.INSTALL_ARGUMENT}")
    announce(styling.muted("      installs Windows, once"))
    announce("")
    announce(f"  {scripts[launcher.RUN_SCRIPT]}")
    announce(styling.muted("      starts the machine, every time after that"))

    if configuration.get(devices.POINTER) == devices.TABLET:
        return

    announce("")
    announce(styling.muted(f"  {devices.GRAB_RELEASE} releases the mouse"))


def configured():
    frames.prepare()

    prompting.take_screen()
    prompting.begin()

    identifier = choose_guest()
    definition = loading.load(identifier)
    guest = loading.document(definition, GUEST_DOCUMENT)

    prompting.begin(header_for(guest))

    name = ask_machine_name(identifier)

    prompting.repin(header_for(guest, name))

    directory = os.path.join(ask_location(), name)
    disc_path = media.ask_disc(guest)
    product_key = media.ask_product_key(guest)

    heading("Hardware")
    report_sharing()
    configuration = asking.ask_all(hardware_groups(definition))

    heading("Installation")
    declarations = guest_questions(definition)
    answers = asking.ask_all(declarations)

    floppy_path = media.floppy_for(disc_path, guest)

    prompting.end()

    summary.show(
        TITLE,
        summary_rows(identifier, name, directory, disc_path, configuration, answers),
    )

    announce("")

    if not confirm.ask("Build it"):
        announce(styling.warning(ABANDONED))

        return 1

    if not may_overwrite(directory):
        announce(styling.warning(ABANDONED))

        return 1

    content = answerfile.built_bytes(guest, declarations, answers, product_key)

    announce("")

    bar = progress.new("preparing", len(building.planned_steps(configuration)))

    built = building.build(
        identifier,
        guest,
        configuration,
        content,
        disc_path,
        directory,
        floppy_path,
        lambda caption: progress.step(bar, 1, caption),
    )

    progress.finish(bar)
    report_built(built)

    install_command = commands.build(configuration, built, boot_from="floppy")
    run_command = commands.build(configuration, running_paths(built), boot_from=drives.SYSTEM_DISK)
    scripts = launcher.scripts_for(directory, install_command, run_command)

    report_scripts(scripts, configuration)

    announce("")

    if not confirm.ask("Start the installation now"):
        where = scripts[launcher.RUN_SCRIPT]

        announce(
            styling.muted(f"  nothing started; run {where} {launcher.INSTALL_ARGUMENT} when ready")
        )

        return 0

    launcher.start(install_command, directory)
    announce(styling.success("  the machine is starting"))

    return 0


def main():
    try:
        return configured()
    except KeyboardInterrupt:
        prompting.end()
        announce(styling.warning(INTERRUPTED))

        return 1
    finally:
        prompting.end()


if __name__ == "__main__":
    sys.exit(main())
