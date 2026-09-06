import os
import tomllib

GUESTS_DIRECTORY = "guests"
ASSETS_DIRECTORY = "assets"

DOCUMENT_SUFFIX = ".toml"
GUEST_DOCUMENT = "guest"

HANDLER_FILE = "handling.py"
HANDLER_MODULE = "handling"

NOTHING_DECLARED = {}


def root_directory():
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), GUESTS_DIRECTORY)


def directory_of(identifier):
    return os.path.join(root_directory(), identifier)


def assets_directory(identifier):
    return os.path.join(directory_of(identifier), ASSETS_DIRECTORY)


def document_path(identifier, name):
    return os.path.join(directory_of(identifier), name + DOCUMENT_SUFFIX)


def is_a_guest(directory):
    return os.path.isfile(os.path.join(directory, GUEST_DOCUMENT + DOCUMENT_SUFFIX))


def available():
    root = root_directory()

    if not os.path.isdir(root):
        return []

    return sorted(name for name in os.listdir(root) if is_a_guest(os.path.join(root, name)))


def refuse_unknown_guest(identifier):
    if identifier not in available():
        raise FileNotFoundError(
            "{} is not a guest; available guests are {}".format(
                identifier, ", ".join(available()) or "none"
            )
        )


def read_document(path):
    with open(path, "rb") as handle:
        return tomllib.load(handle)


def document_names(identifier):
    directory = directory_of(identifier)

    return sorted(
        name[: -len(DOCUMENT_SUFFIX)]
        for name in os.listdir(directory)
        if name.endswith(DOCUMENT_SUFFIX)
    )


def documents_of(identifier):
    return {
        name: read_document(document_path(identifier, name)) for name in document_names(identifier)
    }


def handler_path(identifier):
    return os.path.join(directory_of(identifier), HANDLER_FILE)


def has_handler(identifier):
    return os.path.isfile(handler_path(identifier))


def handler_of(identifier):
    if not has_handler(identifier):
        return None

    import importlib.util

    specification = importlib.util.spec_from_file_location(
        f"{identifier}.{HANDLER_MODULE}", handler_path(identifier)
    )
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)

    return module


def load(identifier):
    refuse_unknown_guest(identifier)

    return {
        "identifier": identifier,
        "directory": directory_of(identifier),
        "documents": documents_of(identifier),
        "handler": handler_of(identifier),
    }


def document(definition, name):
    return definition["documents"].get(name, NOTHING_DECLARED)


def declares(definition, name):
    return name in definition["documents"]
