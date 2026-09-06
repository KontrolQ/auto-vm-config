HANDLE = "handle"
OFFSET = "offset"


def on(handle, offset=0):
    return {HANDLE: handle, OFFSET: offset}


def within(region, offset):
    return on(region[HANDLE], region[OFFSET] + offset)


def placed_at(region, at):
    region[HANDLE].seek(region[OFFSET] + at)


def read(region, at, length):
    placed_at(region, at)

    return region[HANDLE].read(length)


def write(region, at, data):
    placed_at(region, at)
    region[HANDLE].write(data)


def fill(region, at, length, value=0):
    write(region, at, bytes([value]) * length)
