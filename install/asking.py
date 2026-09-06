from cli_widgets.widgets import checklist, choice, entry

from definitions import updates
from install import validation

KEY = "key"
QUESTION = "question"
KIND = "kind"
OPTIONS = "options"
DEFAULT = "default"
PLACEHOLDER = "placeholder"
PATTERN = "pattern"
LIMIT = "limit"
REQUIRED = "required"
OPTIONAL = "optional"
VALUE = "value"

CHOICE = "choice"
ENTRY = "entry"
PATH = "path"
FOLDER = "folder"
FILE = "file"

FIRST_POSITION = 0


def kind_of(declaration):
    return declaration.get(KIND, ENTRY)


def options_of(declaration):
    return declaration.get(OPTIONS, [])


def default_position(declaration):
    wanted = declaration.get(DEFAULT)

    for position, option in enumerate(options_of(declaration)):
        if option[VALUE] == wanted:
            return position

    return FIRST_POSITION


def is_required(declaration):
    return declaration.get(REQUIRED, not declaration.get(OPTIONAL, False))


def pattern_validator(declaration):
    if PATTERN not in declaration:
        return None

    return validation.matching(
        declaration[PATTERN], "that does not match the form this field takes"
    )


def presence_validator(declaration):
    if not is_required(declaration):
        return None

    return validation.required()


def existence_validator(declaration):
    if kind_of(declaration) == PATH or kind_of(declaration) == FOLDER:
        return validation.existing_folder()

    if kind_of(declaration) == FILE:
        return validation.existing_file()

    return None


def validators_for(declaration):
    return [
        validator
        for validator in (
            presence_validator(declaration),
            pattern_validator(declaration),
            existence_validator(declaration),
        )
        if validator is not None
    ]


def validator_for(declaration):
    gathered = validators_for(declaration)

    if not gathered:
        return validation.ACCEPTED

    combined = validation.all_of(*gathered)

    if is_required(declaration):
        return combined

    return validation.optional(combined)


def ask_choice(declaration):
    chosen = choice.ask(
        declaration[QUESTION], options_of(declaration), default_position(declaration)
    )

    return chosen[VALUE]


def ask_entry(declaration, validator=None):
    return entry.ask(
        declaration[QUESTION],
        str(declaration.get(DEFAULT, "")),
        validator or validator_for(declaration),
        declaration.get(PLACEHOLDER, ""),
        declaration.get(LIMIT),
    )


def refuse_unknown_kind(declaration):
    raise ValueError(f"{kind_of(declaration)} is not a kind of question")


def ask(declaration):
    if kind_of(declaration) == CHOICE:
        return ask_choice(declaration)

    if kind_of(declaration) in (ENTRY, PATH, FOLDER, FILE):
        return ask_entry(declaration)

    return refuse_unknown_kind(declaration)


def ask_all(declarations):
    return {declaration[KEY]: ask(declaration) for declaration in declarations}


def update_option(entry_held):
    return {
        "label": entry_held["name"],
        "note": entry_held.get("note", ""),
        VALUE: updates.identifier_of(entry_held),
    }


def ticked_positions(offered, chosen_by_default):
    return [
        position
        for position, held in enumerate(offered)
        if updates.identifier_of(held) in chosen_by_default
    ]


def ask_updates(question, catalogue, configuration):
    offered = updates.offered(catalogue, configuration)

    if not offered:
        return []

    chosen = checklist.ask(
        question,
        [update_option(held) for held in offered],
        ticked_positions(offered, updates.defaults_for(catalogue, configuration)),
    )

    return [held[VALUE] for held in chosen]
