from emulator import binaries
from emulator import devices
from emulator import drives
from emulator import rendering
from emulator import sharing

SHARED_FOLDER = "shared_folder"

LOCALTIME = "localtime"

DEFAULT_BOOT_SOURCE = drives.SYSTEM_DISK

EMULATOR_NOT_FOUND = binaries.SYSTEM_EMULATOR


def emulator_path():
    return binaries.system_emulator() or EMULATOR_NOT_FOUND


def shared_folder_in(configuration):
    return configuration.get(SHARED_FOLDER, "")


def network_options_for(configuration):
    return sharing.netdev_options(shared_folder_in(configuration))


def build(configuration, paths, boot_from=DEFAULT_BOOT_SOURCE, rtc=LOCALTIME, audio_driver=None):
    return (
        [emulator_path()]
        + devices.machine_arguments(configuration)
        + devices.processor_arguments(configuration)
        + devices.memory_arguments(configuration)
        + devices.video_arguments(configuration)
        + devices.sound_arguments(
            configuration, audio_driver or devices.default_audio_driver()
        )
        + devices.network_arguments(configuration, network_options_for(configuration))
        + devices.pointer_arguments(configuration)
        + drives.attached(paths)
        + drives.boot_arguments(boot_from)
        + devices.clock_arguments(rtc)
        + devices.display_arguments()
    )


def sharing_complaint(configuration):
    if not sharing.is_wanted(shared_folder_in(configuration)):
        return sharing.NO_COMPLAINT

    return sharing.complaint()


def as_one_line(command):
    return rendering.as_one_line(command)


def as_grouped_lines(command):
    return rendering.as_grouped_lines(command)
