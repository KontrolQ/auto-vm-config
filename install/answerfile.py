LINE_ENDING = "\r\n"
QUOTE = '"'

ENCODING = "ascii"
UNSUPPORTED_CHARACTERS = "replace"

ANSWERS = "answers"
SECTIONS = "sections"
FILE = "file"
TARGET = "target"

PRODUCT_KEY = "product_key"
SECTION = "section"
FIELD = "field"

QUESTION_KEY = "key"

NOTHING = ""


def is_a_number(value):
    return isinstance(value, int) and not isinstance(value, bool)


def formatted_value(value):
    if is_a_number(value):
        return str(value)

    return QUOTE + str(value) + QUOTE


def line_for(key, value):
    return f"{key}={formatted_value(value)}"


def heading_for(name):
    return f"[{name}]"


def section_lines(name, content):
    if isinstance(content, list):
        return [heading_for(name), *list(content)]

    return [heading_for(name)] + [line_for(key, value) for key, value in content.items()]


def lines_of(document):
    lines = []

    for name, pairs in document.items():
        lines += [*section_lines(name, pairs), ""]

    return lines


def rendered(document):
    return LINE_ENDING.join(lines_of(document))


def encoded(document):
    return rendered(document).encode(ENCODING, UNSUPPORTED_CHARACTERS)


def placed(document, name, key, value):
    held = dict(document)
    held[name] = dict(held.get(name, {}))
    held[name][key] = value

    return held


def settings_of(guest):
    return guest.get(ANSWERS, {})


def file_name(guest):
    return settings_of(guest)[FILE]


def target_of(guest):
    return settings_of(guest)[TARGET]


def declared_sections(guest):
    return {name: dict(pairs) for name, pairs in settings_of(guest).get(SECTIONS, {}).items()}


def is_placed(declaration):
    return SECTION in declaration and FIELD in declaration


def with_answers(document, declarations, answers):
    held = document

    for declaration in declarations:
        if not is_placed(declaration):
            continue

        held = placed(
            held,
            declaration[SECTION],
            declaration[FIELD],
            answers.get(declaration[QUESTION_KEY], NOTHING),
        )

    return held


def key_settings(guest):
    return guest.get(PRODUCT_KEY, {})


def with_product_key(document, guest, product_key):
    settings = key_settings(guest)

    if not is_placed(settings) or not product_key:
        return document

    return placed(document, settings[SECTION], settings[FIELD], product_key)


def with_extra(document, extra):
    if not extra:
        return document

    held = dict(document)
    held.update(extra)

    return held


def build(guest, declarations, answers, product_key, extra=None):
    document = with_answers(declared_sections(guest), declarations, answers)
    document = with_product_key(document, guest, product_key)

    return with_extra(document, extra)


def built_bytes(guest, declarations, answers, product_key, extra=None):
    return encoded(build(guest, declarations, answers, product_key, extra))
