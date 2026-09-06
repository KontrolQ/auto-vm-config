FIELD = "field"

ABOVE = "above"
AT_LEAST = "at_least"
BELOW = "below"
AT_MOST = "at_most"
EQUALS = "equals"
ONE_OF = "one_of"
PRESENT = "present"

COMPARISONS = {
    ABOVE: lambda held, wanted: held > wanted,
    AT_LEAST: lambda held, wanted: held >= wanted,
    BELOW: lambda held, wanted: held < wanted,
    AT_MOST: lambda held, wanted: held <= wanted,
    EQUALS: lambda held, wanted: held == wanted,
    ONE_OF: lambda held, wanted: held in wanted,
    PRESENT: lambda held, wanted: bool(held) == bool(wanted),
}

ALWAYS = None


def refuse_unknown_comparison(name):
    if name not in COMPARISONS:
        raise ValueError(
            "%s is not a comparison; use one of %s"
            % (name, ", ".join(sorted(COMPARISONS)))
        )


def refuse_missing_field(condition):
    if FIELD not in condition:
        raise ValueError("a condition needs a %s to compare" % FIELD)


def comparisons_in(condition):
    return [name for name in condition if name != FIELD]


def holds_for(held, name, wanted):
    refuse_unknown_comparison(name)

    if held is None:
        return False

    return COMPARISONS[name](held, wanted)


def met_by(condition, configuration):
    if condition is ALWAYS:
        return True

    refuse_missing_field(condition)

    held = configuration.get(condition[FIELD])

    return all(
        holds_for(held, name, condition[name]) for name in comparisons_in(condition)
    )
