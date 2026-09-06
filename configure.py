import os
import sys

import clock
from catalogue import addresses
from catalogue import gathering
from definitions import loading
from definitions import updates
from emulator import commands
from emulator import devices
from emulator import drives
from emulator import launcher
from emulator import sharing
from install import answerfile
from install import asking
from install import building
from install import media
from install import staging
from cli_widgets.rendering import frames
from cli_widgets.rendering import styling
from cli_widgets.widgets import browser
from cli_widgets.widgets import choice
from cli_widgets.widgets import confirm
from cli_widgets.widgets import progress
from cli_widgets.widgets import prompting
from cli_widgets.widgets import summary

GUEST_DOCUMENT = "guest"
HARDWARE_DOCUMENT = "hardware"
QUESTIONS_DOCUMENT = "questions"
UPDATES_DOCUMENT = "updates"

GROUPS = "group"
QUESTIONS = "question"

SHARED_FOLDER = "shared_folder"

NAME_PATTERN = "^[A-Za-z0-9][A-Za-z0-9._-]{0,31}$"
NAME_LIMIT = 32

FETCH_TROUBLE = (OSError, LookupError, ValueError)

NOTHING_SHOWN = -1
EMPTY_BAR = 1


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

    return choice.ask("What should be installed", guest_options(available))[
        asking.VALUE
    ]


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
    announce(styling.warning("  %s already holds files" % directory))

    return confirm.ask("Overwrite what is there", False)


def hardware_groups(definition):
    declared = loading.document(definition, HARDWARE_DOCUMENT).get(GROUPS, [])

    if sharing.is_supported():
        return declared

    return [group for group in declared if group[asking.KEY] != SHARED_FOLDER]


def guest_questions(definition):
    return loading.document(definition, QUESTIONS_DOCUMENT).get(QUESTIONS, [])


def report_sharing():
    if sharing.is_supported():
        return

    remark(sharing.complaint())
    remark("files can be placed on the second disk instead")


def summary_rows(identifier, name, directory, disc_path, configuration, answers, chosen):
    rows = [
        ("Guest", identifier),
        ("Machine", name),
        ("Folder", directory),
        ("Disc", disc_path),
    ]

    rows += [(key.replace("_", " ").capitalize(), value) for key, value in configuration.items()]
    rows += [(key.replace("_", " ").capitalize(), value or "-") for key, value in answers.items()]
    rows += [("Clock", "host, %s" % clock.described_offset())]
    rows += [("Updates chosen", len(chosen))]

    return rows


def install_sequence(catalogue, chosen):
    return [held["name"] for held in updates.sequence_for(catalogue, chosen)]


def sequence_lines(catalogue, chosen):
    ordered = install_sequence(catalogue, chosen)

    if not ordered:
        return []

    return ["", styling.bold(styling.underlined("Update order"))] + [
        "  %2d. %s" % (position, name)
        for position, name in enumerate(ordered, start=1)
    ]


def report_built(built):
    announce("")
    announce(styling.bold(styling.underlined("Written")))
    announce("")

    for name, path in built.items():
        announce("  %-14s %s" % (name.replace("_", " "), path))


def guest_updates(guest):
    return guest.get("updates", {})


def staged_files(identifier, guest, survey):
    if not staging.present(survey):
        return {}

    settings = guest_updates(guest)
    inside = settings["directory"].split("\\")[-1]

    staged = staging.staged_files(survey, inside)
    staged[inside + "/" + settings["runner"]] = staging.runner_for(
        identifier,
        survey,
        settings["directory"],
        settings["runner_asset"],
        settings["step_asset"],
    )

    return staged


def answer_extra(guest, survey):
    if not staging.present(survey):
        return None

    return guest_updates(guest).get("answer_lines")


def running_paths(built):
    return {
        name: path
        for name, path in built.items()
        if name in (drives.SYSTEM_DISK, drives.DATA_DISK)
    }


def report_scripts(scripts, configuration):
    announce("")
    announce(styling.bold(styling.underlined("To launch")))
    announce("")
    announce("  %s %s" % (scripts[launcher.RUN_SCRIPT], launcher.INSTALL_ARGUMENT))
    announce(styling.muted("      installs Windows, once"))
    announce("")
    announce("  %s" % scripts[launcher.RUN_SCRIPT])
    announce(styling.muted("      starts the machine, every time after that"))

    if configuration.get(devices.POINTER) == devices.TABLET:
        return

    announce("")
    announce(styling.muted("  %s releases the mouse" % devices.GRAB_RELEASE))


def ask_updates_folder(wanted):
    if not wanted:
        return ""

    heading("Update installers")
    remark("%d of the updates chosen are not in the catalogue" % len(wanted))
    remark("they install only if you already have their installer files")

    if not confirm.ask("Do you have the installer files", False):
        return ""

    return browser.ask_folder("Folder holding the installer files", os.getcwd())


def stepper(bar):
    shown = [NOTHING_SHOWN]

    def advanced(amount):
        progress.advanced(bar, amount)

        if progress.percentage_of(bar) != shown[0]:
            shown[0] = progress.percentage_of(bar)
            progress.show(bar)

    return advanced


def fetch_one(entry, record):
    bar = progress.new(entry["name"], gathering.size_of(record) or EMPTY_BAR)

    try:
        path = gathering.fetch(entry, record, stepper(bar))
    except BaseException:
        frames.finish()

        raise

    progress.finish(bar)

    return path


def report_fetched(entry, record, held):
    if gathering.verifiable(record):
        announce(styling.success("  %s %s" % (entry["name"], held)))

        return

    announce(
        styling.warning(
            "  %s carries no published checksum and was taken as it came" % entry["name"]
        )
    )


def fetch_update(entry):
    record = gathering.record_for(entry)
    cached = gathering.cached(entry, record)
    path = cached or fetch_one(entry, record)

    report_fetched(entry, record, "already downloaded" if cached else "downloaded")

    return path


def fetch_updates(wanted):
    catalogued = gathering.catalogued(wanted)

    if not catalogued:
        return {}

    announce("")
    announce(styling.bold(styling.underlined("Downloads")))
    announce("")
    announce(
        styling.muted(
            "  installers come from %s and are kept for the next build" % addresses.SITE
        )
    )
    announce("")

    held = {}

    for entry in catalogued:
        try:
            held[updates.identifier_of(entry)] = fetch_update(entry)
        except FETCH_TROUBLE as refused:
            announce(
                styling.warning("  %s was not installed: %s" % (entry["name"], refused))
            )

    return held


def report_survey(survey, target):
    announce("")
    announce(styling.bold(styling.underlined("Updates")))
    announce("")

    for held in staging.present(survey):
        announce(
            "  %s %-40s %s"
            % (
                styling.success("will install"),
                held["entry"]["name"],
                styling.muted(held["entry"].get("file", "")),
            )
        )

    for held in staging.absent(survey):
        announce(
            "  %s %-40s %s"
            % (
                styling.warning("skipped".ljust(len("will install"))),
                held["entry"]["name"],
                styling.muted(
                    "%s not found" % held["entry"].get("file", "its installer")
                ),
            )
        )

    if gathering.uncatalogued([held["entry"] for held in staging.absent(survey)]):
        announce("")
        announce(
            styling.muted(
                "  skipped updates need their installer put in the folder you point at"
            )
        )

    if staging.present(survey):
        announce("")
        announce(
            styling.muted(
                "  copied to %s and run when Windows first starts" % target
            )
        )


def configured():
    frames.prepare()

    prompting.take_screen()
    prompting.begin()

    identifier = choose_guest()
    definition = loading.load(identifier)
    guest = loading.document(definition, GUEST_DOCUMENT)
    catalogue = loading.document(definition, UPDATES_DOCUMENT)

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

    heading("Updates")
    chosen = asking.ask_updates("Updates to install", catalogue, configuration)

    floppy_path = media.floppy_for(disc_path, guest)

    prompting.end()

    summary.show(
        TITLE,
        summary_rows(
            identifier, name, directory, disc_path, configuration, answers, chosen
        ),
    )

    for line in sequence_lines(catalogue, chosen):
        announce(line)

    announce("")

    if not confirm.ask("Build it"):
        announce(styling.warning(ABANDONED))

        return 1

    if not may_overwrite(directory):
        announce(styling.warning(ABANDONED))

        return 1

    wanted = updates.sequence_for(catalogue, chosen)
    folder = ask_updates_folder(gathering.uncatalogued(wanted))
    survey = staging.surveyed(wanted, folder, fetch_updates(wanted))
    staged = staged_files(identifier, guest, survey)

    report_survey(survey, guest["updates"]["directory"])

    content = answerfile.built_bytes(
        guest, declarations, answers, product_key, answer_extra(guest, survey)
    )

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
        staged,
    )

    progress.finish(bar)
    report_built(built)

    install_command = commands.build(configuration, built, boot_from="floppy")
    run_command = commands.build(
        configuration, running_paths(built), boot_from=drives.SYSTEM_DISK
    )
    scripts = launcher.scripts_for(directory, install_command, run_command)

    report_scripts(scripts, configuration)

    announce("")

    if not confirm.ask("Start the installation now"):
        announce(
            styling.muted(
                "  nothing started; run %s %s when ready"
                % (scripts[launcher.RUN_SCRIPT], launcher.INSTALL_ARGUMENT)
            )
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
