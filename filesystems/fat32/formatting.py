from filesystems.directories import entries
from filesystems.fat32 import bootsector
from filesystems.fat32 import information
from filesystems.fat32 import sizing
from filesystems.fat32 import table
from filesystems.naming import labels

ROOT_DIRECTORY_CLUSTERS = 1
NO_FIRST_CLUSTER = 0
NO_SIZE = 0


def first_table_sector():
    return sizing.RESERVED_SECTORS


def table_sector_for(position, sectors_per_table):
    return first_table_sector() + position * sectors_per_table


def first_data_sector(sectors_per_table):
    return first_table_sector() + sizing.TABLES_PRESENT * sectors_per_table


def free_clusters_in(plan):
    return plan["clusters"] - ROOT_DIRECTORY_CLUSTERS


def first_free_cluster():
    return table.FIRST_DATA_CLUSTER + ROOT_DIRECTORY_CLUSTERS


def root_directory_sector(volume_label, moment):
    sector = bytearray(sizing.BYTES_PER_SECTOR)

    sector[: entries.ENTRY_SIZE] = entries.with_raw_name(
        labels.encoded(volume_label),
        entries.VOLUME_LABEL,
        NO_FIRST_CLUSTER,
        NO_SIZE,
        moment,
    )

    return bytes(sector)


def reserved_sectors_of(
    plan,
    first_partition_sector,
    sectors_per_track,
    heads_per_cylinder,
    volume_label,
    serial_number,
):
    boot = bootsector.build(
        plan["partition_sectors"],
        plan["sectors_per_cluster"],
        plan["sectors_per_table"],
        first_partition_sector,
        sectors_per_track,
        heads_per_cylinder,
        volume_label,
        serial_number,
        sizing.TABLES_PRESENT,
        sizing.RESERVED_SECTORS,
    )
    details = information.build(free_clusters_in(plan), first_free_cluster())

    return [
        (0, boot),
        (bootsector.INFORMATION_SECTOR, details),
        (bootsector.BACKUP_SECTOR, boot),
        (bootsector.BACKUP_SECTOR + bootsector.INFORMATION_SECTOR, details),
    ]


def table_sectors_of(plan):
    populated = table.first_sector(ROOT_DIRECTORY_CLUSTERS)

    return [
        (table_sector_for(position, plan["sectors_per_table"]), populated)
        for position in range(sizing.TABLES_PRESENT)
    ]


def data_sectors_of(plan, volume_label, moment):
    return [
        (
            first_data_sector(plan["sectors_per_table"]),
            root_directory_sector(volume_label, moment),
        )
    ]


def sectors_for(
    partition_sectors,
    first_partition_sector,
    sectors_per_track,
    heads_per_cylinder,
    volume_label,
    serial_number,
    moment,
):
    plan = sizing.plan_for(partition_sectors)

    return (
        reserved_sectors_of(
            plan,
            first_partition_sector,
            sectors_per_track,
            heads_per_cylinder,
            volume_label,
            serial_number,
        )
        + table_sectors_of(plan)
        + data_sectors_of(plan, volume_label, moment)
    )
