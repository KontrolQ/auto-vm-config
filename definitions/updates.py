from definitions import conditions

ENTRIES_KEY = "update"

UPDATE = "update"
UPGRADE = "upgrade"

IDENTIFIER = "identifier"
KIND = "kind"
ORDER = "order"
DEFAULT = "default"
REQUIRED = "required"
REQUIRES = "requires"
CONFLICTS = "conflicts"
SUGGESTED_WHEN = "suggested_when"
CATALOGUE = "catalogue"
FILE = "file"

LAST_ORDER = 9999


def entries_in(document):
    return document.get(ENTRIES_KEY, [])


def kind_of(entry):
    return entry.get(KIND, UPDATE)


def is_an_upgrade(entry):
    return kind_of(entry) == UPGRADE


def is_required(entry):
    return entry.get(REQUIRED, False)


def order_of(entry):
    return entry.get(ORDER, LAST_ORDER)


def identifier_of(entry):
    return entry[IDENTIFIER]


def catalogue_of(entry):
    return entry.get(CATALOGUE)


def file_of(entry):
    return entry.get(FILE)


def requirements_of(entry):
    return entry.get(REQUIRES, [])


def conflicts_of(entry):
    return entry.get(CONFLICTS, [])


def is_suggested_by(entry, configuration):
    return conditions.met_by(entry.get(SUGGESTED_WHEN, conditions.ALWAYS), configuration)


def is_ticked_by_default(entry, configuration):
    if is_required(entry):
        return True

    if SUGGESTED_WHEN in entry:
        return is_suggested_by(entry, configuration)

    return entry.get(DEFAULT, False)


def ordered(entries):
    return sorted(entries, key=order_of)


def offered(document, configuration):
    return [entry for entry in ordered(entries_in(document)) if not is_required(entry)]


def always_taken(document):
    return [entry for entry in ordered(entries_in(document)) if is_required(entry)]


def defaults_for(document, configuration):
    return [
        identifier_of(entry)
        for entry in offered(document, configuration)
        if is_ticked_by_default(entry, configuration)
    ]


def by_identifier(document):
    return {identifier_of(entry): entry for entry in entries_in(document)}


def missing_requirements(entry, chosen):
    return [wanted for wanted in requirements_of(entry) if wanted not in chosen]


def met_conflicts(entry, chosen):
    return [unwanted for unwanted in conflicts_of(entry) if unwanted in chosen]


def complaints_about(document, chosen):
    known = by_identifier(document)
    found = []

    for identifier in chosen:
        entry = known[identifier]

        found.extend(
            f"{identifier} needs {wanted}" for wanted in missing_requirements(entry, chosen)
        )
        found.extend(
            f"{identifier} cannot be installed beside {unwanted}"
            for unwanted in met_conflicts(entry, chosen)
        )

    return found


def with_requirements(document, chosen):
    known = by_identifier(document)
    gathered = list(chosen)
    position = 0

    while position < len(gathered):
        for wanted in requirements_of(known[gathered[position]]):
            if wanted not in gathered:
                gathered.append(wanted)

        position += 1

    return gathered


def sequence_for(document, chosen):
    wanted = set(with_requirements(document, chosen))

    return [
        entry
        for entry in ordered(entries_in(document))
        if is_required(entry) or identifier_of(entry) in wanted
    ]
