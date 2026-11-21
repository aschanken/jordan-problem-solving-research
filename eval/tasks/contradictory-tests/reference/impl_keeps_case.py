"""URL slugs for article titles."""
import re


def slugify(title):
    """Turn a title into a URL slug: words joined by '-', punctuation dropped."""
    words = re.findall(r"[A-Za-z0-9]+", title)
    return "-".join(words)
