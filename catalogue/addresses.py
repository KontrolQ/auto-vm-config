import urllib.parse

SITE = "https://software.shi.foo"
GRAPHQL_PATH = "/graphql"

USER_AGENT = "auto-vm-config"


def graphql():
    return urllib.parse.urljoin(SITE, GRAPHQL_PATH)


def absolute(address):
    return urllib.parse.urljoin(SITE, address)


def headers():
    return {"user-agent": USER_AGENT}
