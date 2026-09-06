import hashlib

ALGORITHMS = {
    "MD5": hashlib.md5,
    "SHA1": hashlib.sha1,
    "SHA224": hashlib.sha224,
    "SHA256": hashlib.sha256,
    "SHA384": hashlib.sha384,
    "SHA512": hashlib.sha512,
}

SEPARATORS = "-_ \t"

BLOCK = 1024 * 1024


def named(algorithm):
    held = str(algorithm or "").upper()

    for separator in SEPARATORS:
        held = held.replace(separator, "")

    return held


def supported(algorithm):
    return named(algorithm) in ALGORITHMS


def digest_for(algorithm):
    return ALGORITHMS[named(algorithm)]()


def agree(held, expected):
    return held.lower() == expected.lower()


def of_file(path, algorithm):
    digest = digest_for(algorithm)

    with open(path, "rb") as reading:
        for block in iter(lambda: reading.read(BLOCK), b""):
            digest.update(block)

    return digest.hexdigest()


def matches(path, algorithm, expected):
    return agree(of_file(path, algorithm), expected)
