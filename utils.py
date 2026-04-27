import secrets
import ipaddress
from urllib.parse import urlparse


CODE_LENGTH = 6
BASE62_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


def is_valid_url(url: str) -> bool:
    """
    Slightly stronger URL validation while still beginner-friendly:
    - no spaces
    - max length check
    - scheme must be http/https
    - host must exist and contain no whitespace
    - optional port must be valid
    """
    if not url or " " in url or len(url) > 2048:
        return False

    parsed_url = urlparse(url)
    if parsed_url.scheme not in {"http", "https"}:
        return False
    if not parsed_url.netloc or not parsed_url.hostname:
        return False
    if any(ch.isspace() for ch in parsed_url.netloc):
        return False

    hostname = parsed_url.hostname
    if not _is_valid_host(hostname):
        return False

    try:
        _ = parsed_url.port
    except ValueError:
        return False

    return True


def _is_valid_host(hostname: str) -> bool:
    """Validate host as localhost, IP, or common domain format."""
    if hostname == "localhost":
        return True

    try:
        ipaddress.ip_address(hostname)
        return True
    except ValueError:
        pass

    labels = hostname.split(".")
    if len(labels) < 2:
        return False

    for label in labels:
        if not label or len(label) > 63:
            return False
        if label[0] == "-" or label[-1] == "-":
            return False
        if not all(ch.isalnum() or ch == "-" for ch in label):
            return False

    return True


def int_to_base62(number: int) -> str:
    """Convert an integer to a Base62 string."""
    if number == 0:
        return BASE62_ALPHABET[0]

    encoded = []
    base = len(BASE62_ALPHABET)
    while number > 0:
        number, remainder = divmod(number, base)
        encoded.append(BASE62_ALPHABET[remainder])

    return "".join(reversed(encoded))


def generate_short_code(length: int = CODE_LENGTH) -> str:
    """
    Generate a fixed-length Base62 short code.
    Uses secure randomness, then Base62-encodes it.
    """
    max_base62_value = len(BASE62_ALPHABET) ** length
    random_number = secrets.randbelow(max_base62_value)
    base62_code = int_to_base62(random_number)

    # Left-pad with "0" (Base62 zero) so code is always exactly `length`.
    return base62_code.rjust(length, BASE62_ALPHABET[0])


def is_valid_custom_code(custom_code: str) -> bool:
    """Validate custom short code format (alphanumeric, length 3-20)."""
    if not custom_code:
        return False
    if len(custom_code) < 3 or len(custom_code) > 20:
        return False
    return custom_code.isalnum()
