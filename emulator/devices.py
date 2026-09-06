import sys

PROCESSOR = "processor"
MEMORY = "memory_megabytes"
VIDEO = "video"
SOUND = "sound"
NETWORK = "network"
POWER_MANAGEMENT = "power_management"
POINTER = "pointer"

DISPLAY_BACKEND = "sdl"
GRAB_MODIFIER = "rctrl"
GRAB_RELEASE = "right ctrl + g"

TABLET = "tablet"
TABLET_DEVICE = "usb-tablet"

MACHINE = "pc"
ACPI = "acpi"
APM = "apm"

NONE = "none"

SOUND_DEVICES = {
    "sb16": "sb16",
    "es1370": "ES1370",
    "ac97": "AC97",
}

AUDIO_BACKEND = "audio0"

WINDOWS_AUDIO_DRIVER = "dsound"
MACOS_AUDIO_DRIVER = "coreaudio"
UNIX_AUDIO_DRIVER = "pa"

NETWORK_BACKEND = "net0"


def default_audio_driver():
    if sys.platform == "win32":
        return WINDOWS_AUDIO_DRIVER

    if sys.platform == "darwin":
        return MACOS_AUDIO_DRIVER

    return UNIX_AUDIO_DRIVER


def machine_arguments(configuration):
    if configuration.get(POWER_MANAGEMENT, APM) == ACPI:
        return ["-machine", MACHINE]

    return ["-machine", f"{MACHINE},{ACPI}=off"]


def processor_arguments(configuration):
    return ["-cpu", configuration[PROCESSOR]]


def memory_arguments(configuration):
    return ["-m", str(configuration[MEMORY])]


def video_arguments(configuration):
    return ["-vga", configuration.get(VIDEO, NONE)]


def sound_arguments(configuration, audio_driver):
    chosen = configuration.get(SOUND, NONE)

    if chosen == NONE:
        return []

    return [
        "-audiodev",
        f"{audio_driver},id={AUDIO_BACKEND}",
        "-device",
        f"{SOUND_DEVICES[chosen]},audiodev={AUDIO_BACKEND}",
    ]


def backend_options(extra_options):
    return ",".join(["user", f"id={NETWORK_BACKEND}", *list(extra_options)])


def network_arguments(configuration, extra_options=()):
    chosen = configuration.get(NETWORK, NONE)

    if chosen == NONE:
        return []

    return [
        "-netdev",
        backend_options(extra_options),
        "-device",
        f"{chosen},netdev={NETWORK_BACKEND}",
    ]


def clock_arguments(rtc):
    return ["-rtc", f"base={rtc}"]


def display_arguments():
    return ["-display", f"{DISPLAY_BACKEND},grab-mod={GRAB_MODIFIER}"]


def pointer_arguments(configuration):
    if configuration.get(POINTER) != TABLET:
        return []

    return ["-usb", "-device", TABLET_DEVICE]
