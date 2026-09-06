import json
import urllib.request

from catalogue import addresses

TIMEOUT = 30

CONTENT_TYPE = "application/json"
ENCODING = "utf-8"

SOFTWARE = "software"
VERSION = "version"
ITEM = "item"

FILE_QUERY = """
query Held($slug: String!) {
  Software(slug: $slug) {
    name
    versions {
      slug
      version
      files {
        slug
        displayName
        sizeBytes
        checksum
        checksumAlgorithm
        downloadUrl
      }
    }
  }
}
"""


def described(reference):
    return "%s %s %s" % (
        reference[SOFTWARE],
        reference[VERSION],
        reference[ITEM],
    )


def sent(query, variables):
    body = json.dumps({"query": query, "variables": variables}).encode(ENCODING)
    headers = dict(addresses.headers(), **{"content-type": CONTENT_TYPE})
    request = urllib.request.Request(addresses.graphql(), data=body, headers=headers)

    with urllib.request.urlopen(request, timeout=TIMEOUT) as answer:
        return json.loads(answer.read().decode(ENCODING))


def refuse_complaints(held):
    complaints = held.get("errors") or []

    if complaints:
        raise LookupError(complaints[0].get("message", "the catalogue refused to answer"))


def named(entries, wanted):
    for held in entries:
        if held["slug"] == wanted:
            return held

    return None


def software_in(held, reference):
    found = (held.get("data") or {}).get("Software")

    if found is None:
        raise LookupError("the catalogue holds nothing called %s" % reference[SOFTWARE])

    return found


def version_in(software, reference):
    found = named(software["versions"], reference[VERSION])

    if found is None:
        raise LookupError(
            "%s has no version %s" % (reference[SOFTWARE], reference[VERSION])
        )

    return found


def file_in(version, reference):
    found = named(version["files"], reference[ITEM])

    if found is None:
        raise LookupError("%s holds no file called %s" % (described(reference), reference[ITEM]))

    return found


def looked_up(reference):
    held = sent(FILE_QUERY, {"slug": reference[SOFTWARE]})

    refuse_complaints(held)

    software = software_in(held, reference)

    return file_in(version_in(software, reference), reference)
