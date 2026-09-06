import os
import re

ACCEPTED = None


def accepted():
    return ACCEPTED


def required(complaint="a value is required"):
    def check(value):
        if not str(value).strip():
            return complaint

        return ACCEPTED

    return check


def matching(pattern, complaint):
    expression = re.compile(pattern)

    def check(value):
        if expression.match(str(value)):
            return ACCEPTED

        return complaint

    return check


def existing_file(complaint="no file of that name is on this machine"):
    def check(value):
        if os.path.isfile(str(value)):
            return ACCEPTED

        return complaint

    return check


def existing_folder(complaint="no folder of that name is on this machine"):
    def check(value):
        if os.path.isdir(str(value)):
            return ACCEPTED

        return complaint

    return check


def optional(validator):
    def check(value):
        if not str(value).strip():
            return ACCEPTED

        return validator(value)

    return check


def all_of(*validators):
    def check(value):
        for validator in validators:
            complaint = validator(value)

            if complaint is not ACCEPTED:
                return complaint

        return ACCEPTED

    return check
