import re
import os
from urllib.parse import urlparse

def is_valid_url(url: str) -> bool:
    """
    Function to sanitize a url field
    """
    try:
        parsed = urlparse(url)
        # if the address do not start with http or https
        if parsed.scheme not in ('http', 'https'):
            return False
        # minimum domain existence check
        if not parsed.netloc:
            return False
        # check that the address has a TLD
        if not re.match(r".+\.[a-zA-Z]{2,}$", parsed.netloc):
            return False
        # In case than you dont want to accept IP local addresses, uncomment this:
        #if re.match(r"^(localhost|127\.0\.0\.1|192\.168\.|10\.)", parsed.netloc):
        #    return False
        return True
    except Exception:
        return False
    
def is_valid_name(name: str, max_length: int) -> bool:
    """
    Function to sanitize a name field:
        - Do not be empty
        - Have length between 1 and `max_length`.
        - Contain only letters, numbers, spaces, hyphens and underscores
    """
    name = name.strip()

    # min/max length
    if not (1 <= len(name) <= max_length):
        return False

    # do not allow: < > { } ^ ~ ` ,if you want to restrict more change to r"^[\w\s\-,]+$" this only allow numbers, letters,# do not allow: < > { } ^ ~ ` ,if you want to restrict more change to r"^[\w\s\-,]+$" this only allow numbers, letters, comma, hyphen and underscore
    if not re.match(r"^[^<>{}^~`]+$", name, re.UNICODE):
        return False
    return True
