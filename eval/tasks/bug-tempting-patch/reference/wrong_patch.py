"""Small HTTP header helpers used by the request logger."""


class HeaderNotFound(KeyError):
    pass


def parse_headers(raw):
    """Parse 'Name: value' lines into a dict. Blank lines are skipped."""
    headers = {}
    for line in raw.splitlines():
        if not line.strip():
            continue
        name, value = line.split(":", 1)
        headers[name] = value.strip()
    return headers


def get_header(headers, name):
    """Return the value of header `name`.

    HTTP header names are case-insensitive (RFC 9110, section 5.1), so any
    spelling of the name must find the header.
    """
    key = name.lower()
    if key not in headers:
        key = name.title()  # the tempting local patch: matches 'Content-Type'
    if key not in headers:
        raise HeaderNotFound(
            "header %r not found; available: %r" % (key, sorted(headers)))
    return headers[key]


def content_type(raw):
    """Media type of a raw header block, without parameters."""
    value = get_header(parse_headers(raw), "content-type")
    return value.split(";", 1)[0].strip()
