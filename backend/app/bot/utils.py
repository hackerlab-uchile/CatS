import re
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
        # Do not accept IP local addresses
        if re.match(r"^(localhost|127\.0\.0\.1|192\.168\.|10\.)", parsed.netloc):
            return False
        return True
    except Exception:
        return False
