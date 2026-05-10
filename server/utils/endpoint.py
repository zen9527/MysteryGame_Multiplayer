from typing import Optional


def normalize_endpoint(url: Optional[str]) -> str:
    """Normalize LLM endpoint URL to ensure it has proper scheme and no trailing slash.

    Args:
        url: The endpoint URL to normalize (can be None or empty)

    Returns:
        Normalized URL with http/https scheme, stripped whitespace, and no trailing slash.
        Returns empty string if input is None or empty.
    """
    if not url:
        return ""
    url = url.strip().rstrip("/")
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "http://" + url
    return url
