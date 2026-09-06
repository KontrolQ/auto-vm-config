import os

import clock
from definitions import assets
from disks import creation
from disks import geometry
from filesystems import regions
from filesystems.fat12 import files as floppy_files
from filesystems.fat12 import layout as floppy_layout
from filesystems.fat32 import files as disk_files
from filesystems.fat32 import layout as disk_layout
from install import answerfile
from media.eltorito import chooser
from media.eltorito import images

SYSTEM_IMAGE = "system.img"
DATA_IMAGE = "data.img"
FLOPPY_IMAGE = "boot.img"

SYSTEM_LABEL = "SYSTEM"
DATA_LABEL = "DATA"

BYTES_PER_GIGABYTE = 1024 * 1024 * 1024

SYSTEM_DISK_KEY = "system_disk_gigabytes"
DATA_DISK_KEY = "data_disk_gigabytes"

FLOPPY_TARGET = "floppy"
SYSTEM_TARGET = "system_disk"

NO_DATA_DISK = 0


def serial_from(moment):
    return int(moment.timestamp()) & 0xFFFFFFFF


def prepared_directory(directory):
    os.makedirs(directory, exist_ok=True)

    return directory


def image_path(directory, name):
    return os.path.join(directory, name)


def bytes_for(gigabytes):
    return gigabytes * BYTES_PER_GIGABYTE


def create_disk(path, gigabytes, label, moment, bootable):
    return creation.create(
        path, bytes_for(gigabytes), label, serial_from(moment), moment, bootable
    )


def opened_volume(path, first_partition_sector):
    handle = open(path, "r+b")

    return handle, regions.on(handle, geometry.offset_of_sector(first_partition_sector))


def stage_onto_disk(path, first_partition_sector, staged, moment):
    handle, region = opened_volume(path, first_partition_sector)

    try:
        parameters = disk_layout.parameters(region)

        for name, content in staged.items():
            disk_files.write(region, parameters, name, content, moment)
    finally:
        handle.close()


def boot_floppy_from_disc(disc_path):
    with open(disc_path, "rb") as handle:
        if not images.carries_a_boot_floppy(handle):
            return None

        return chooser.without(images.extracted(handle))


def supplied_floppy(path):
    with open(path, "rb") as handle:
        return handle.read()


def stage_onto_floppy(image, staged):
    held = bytearray(image)
    parameters = floppy_layout.parameters(held)
    moment = clock.now()

    for name, content in staged.items():
        floppy_files.write(held, parameters, name, content, moment)

    return bytes(held)


def startup_values(guest):
    return {
        "setup_directory": guest["setup"]["directory"],
        "setup_program": guest["setup"]["program"],
        "setup_arguments": guest["setup"]["arguments"],
        "answer_file": "A:\\" + answerfile.file_name(guest),
    }


def startup_file(identifier, guest):
    settings = guest["boot"]

    return settings["startup_target"], assets.prepared(
        identifier, settings["startup_asset"], startup_values(guest)
    )


def floppy_staging(identifier, guest, answers_content):
    target, startup = startup_file(identifier, guest)

    return {
        target: startup,
        answerfile.file_name(guest): answers_content,
    }


def disk_staging(guest, answers_content, extra_files):
    staged = dict(extra_files or {})

    if answerfile.target_of(guest) == SYSTEM_TARGET:
        staged[answerfile.file_name(guest)] = answers_content

    return staged


def wants_a_data_disk(configuration):
    return configuration.get(DATA_DISK_KEY, NO_DATA_DISK) > NO_DATA_DISK


def planned_steps(configuration):
    captions = ["creating the system disk", "writing the answer file"]

    if wants_a_data_disk(configuration):
        captions.append("creating the second disk")

    return captions + ["preparing the boot floppy"]


def noted(watcher, caption):
    if watcher is not None:
        watcher(caption)


def build(
    identifier,
    guest,
    configuration,
    answers_content,
    disc_path,
    directory,
    floppy_path=None,
    watcher=None,
    extra_files=None,
):
    moment = clock.now()

    prepared_directory(directory)

    built = {}

    noted(watcher, "creating the system disk")

    system_path = image_path(directory, SYSTEM_IMAGE)
    system = create_disk(
        system_path, configuration[SYSTEM_DISK_KEY], SYSTEM_LABEL, moment, True
    )

    noted(watcher, "writing the answer file")

    stage_onto_disk(
        system_path,
        system["first_partition_sector"],
        disk_staging(guest, answers_content, extra_files),
        moment,
    )
    built["system_disk"] = system_path

    if wants_a_data_disk(configuration):
        noted(watcher, "creating the second disk")

        data_path = image_path(directory, DATA_IMAGE)

        create_disk(
            data_path, configuration[DATA_DISK_KEY], DATA_LABEL, moment, False
        )
        built["data_disk"] = data_path

    noted(watcher, "preparing the boot floppy")

    image = supplied_floppy(floppy_path) if floppy_path else boot_floppy_from_disc(disc_path)

    if image is not None:
        floppy_path_out = image_path(directory, FLOPPY_IMAGE)

        with open(floppy_path_out, "wb") as handle:
            handle.write(
                stage_onto_floppy(
                    image, floppy_staging(identifier, guest, answers_content)
                )
            )

        built["floppy"] = floppy_path_out

    built["disc"] = disc_path

    return built
