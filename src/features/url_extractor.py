"""
src/features/url_extractor.py
Extracts and sanitizes all URLs embedded within raw email subjects, bodies, and HTML content.
Supports the Dual-Representation Pipeline Architecture.
"""

import re
from typing import List

# Comprehensive regex for matching URLs in text and HTML
URL_REGEX = re.compile(
    r'(?:href=[\'"])?(https?://[^\s<>"\')]+|www\.[^\s<>"\')]+)',
    re.IGNORECASE
)

# Trailing punctuation characters commonly attached to URLs in text
TRAILING_PUNCTUATION = '.,;:!?)]}>\'"'

def extract_urls_from_text(text: str) -> List[str]:
    """
    Extracts all unique, valid URLs from raw text or HTML.
    Cleans trailing punctuation and normalizes schemes.
    """
    if not text or not isinstance(text, str):
        return []

    raw_matches = URL_REGEX.findall(text)
    cleaned_urls = []
    seen = set()

    for url in raw_matches:
        # Strip trailing punctuation often caught by regex
        cleaned = url.rstrip(TRAILING_PUNCTUATION)

        # Normalize www. to http://www. for parsing if missing scheme
        if cleaned.lower().startswith('www.'):
            cleaned = 'http://' + cleaned

        # Basic validity check (must have at least a dot)
        if '.' in cleaned and len(cleaned) > 5:
            if cleaned not in seen:
                seen.add(cleaned)
                cleaned_urls.append(cleaned)

    return cleaned_urls
