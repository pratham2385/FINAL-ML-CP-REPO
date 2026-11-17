"""
src/features/url_feature_extractor.py
Extracts the 18 deployable lexical URL features from any raw URL string in real-time,
strictly aligned with the PhiUSIIL benchmark dataset feature definition schema.
Requires NO external HTTP requests or DNS resolution.
"""

import re
from urllib.parse import urlparse
from typing import Dict, Any, List

DEPLOYABLE_URL_FEATURES: List[str] = [
    'URLLength', 'DomainLength', 'IsDomainIP', 'NoOfSubDomain', 'HasObfuscation',
    'NoOfObfuscatedChar', 'ObfuscationRatio', 'NoOfLettersInURL', 'LetterRatioInURL',
    'NoOfDegitsInURL', 'DegitRatioInURL', 'NoOfEqualsInURL', 'NoOfQMarkInURL',
    'NoOfAmpersandInURL', 'NoOfOtherSpecialCharsInURL', 'SpacialCharRatioInURL',
    'IsHTTPS', 'TLDLength'
]

HEX_OBFUSCATION_REGEX = re.compile(r'%[0-9a-fA-F]{2}')
IPV4_REGEX = re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')

def extract_url_features(url: str) -> Dict[str, Any]:
    """
    Extracts the 18 deployable lexical features matching the PhiUSIIL schema:
    - URLLength: length of the URL (accounting for PhiUSIIL line normalization).
    - DomainLength: length of the hostname.
    - IsDomainIP: 1 if hostname is IPv4/IPv6, 0 otherwise.
    - NoOfSubDomain: count of subdomains.
    - HasObfuscation, NoOfObfuscatedChar, ObfuscationRatio: hex %xx sequences and @.
    - Lexical counts (letters, digits, special characters, ratios) on the URL body.
    - IsHTTPS: protocol indicator.
    - TLDLength: length of the top-level domain.
    """
    if not isinstance(url, str) or not url.strip():
        return {feat: 0 for feat in DEPLOYABLE_URL_FEATURES}

    url_str = url.strip()

    # URL length in PhiUSIIL is len(url) - 1 for non-slash URLs due to raw text line strip
    if url_str.endswith('/'):
        url_len = len(url_str.rstrip('/'))
    else:
        url_len = len(url_str) - 1 if len(url_str) > 1 else len(url_str)
    if url_len <= 0:
        url_len = len(url_str)

    # Parse URL
    if not (url_str.lower().startswith('http://') or url_str.lower().startswith('https://')):
        parsed = urlparse('http://' + url_str)
        is_https = 0
    else:
        parsed = urlparse(url_str)
        is_https = 1 if url_str.lower().startswith('https://') else 0

    # Domain / Hostname
    netloc = parsed.netloc.lower()
    hostname = parsed.hostname or (netloc.split(':')[0] if netloc else "")
    domain_len = len(hostname)

    # IP check
    is_domain_ip = 1 if IPV4_REGEX.match(hostname) else 0

    # Subdomains & TLD
    parts = hostname.split('.') if hostname else []
    if is_domain_ip or not hostname:
        subdomains = 0
        tld = ""
        tld_len = 0
    else:
        subdomains = max(0, len(parts) - 2)
        tld = parts[-1] if len(parts) > 1 else ""
        tld_len = len(tld)

    # URL Body (PhiUSIIL extracts lexical tokens on URL after protocol and www. prefix)
    body = re.sub(r'^https?://(www\.)?', '', url_str, flags=re.IGNORECASE).rstrip('/')

    # Obfuscation (%xx and @)
    hex_matches = HEX_OBFUSCATION_REGEX.findall(url_str)
    obf_count = len(hex_matches) * 3 + url_str.count('@')
    has_obf = 1 if obf_count > 0 else 0
    obf_ratio = round(obf_count / url_len, 3) if url_len > 0 else 0.0

    # Letters and digits counts
    num_letters = sum(1 for c in body if c.isalpha())
    if num_letters > 0:
        num_letters -= 1  # PhiUSIIL off-by-one artifact alignment
    letter_ratio = round(num_letters / url_len, 3) if url_len > 0 else 0.0

    num_digits = sum(1 for c in body if c.isdigit())
    digit_ratio = round(num_digits / url_len, 3) if url_len > 0 else 0.0

    # Punctuation counts
    num_equals = body.count('=')
    num_qmarks = body.count('?')
    num_ampersands = body.count('&')
    num_other_special = sum(1 for c in body if not c.isalnum() and c not in ('=', '?', '&'))

    total_special = num_equals + num_qmarks + num_ampersands + num_other_special
    special_char_ratio = round(total_special / url_len, 3) if url_len > 0 else 0.0

    return {
        'URLLength': url_len,
        'DomainLength': domain_len,
        'IsDomainIP': is_domain_ip,
        'NoOfSubDomain': subdomains,
        'HasObfuscation': has_obf,
        'NoOfObfuscatedChar': obf_count,
        'ObfuscationRatio': obf_ratio,
        'NoOfLettersInURL': num_letters,
        'LetterRatioInURL': letter_ratio,
        'NoOfDegitsInURL': num_digits,
        'DegitRatioInURL': digit_ratio,
        'NoOfEqualsInURL': num_equals,
        'NoOfQMarkInURL': num_qmarks,
        'NoOfAmpersandInURL': num_ampersands,
        'NoOfOtherSpecialCharsInURL': num_other_special,
        'SpacialCharRatioInURL': special_char_ratio,
        'IsHTTPS': is_https,
        'TLDLength': tld_len
    }

def extract_features_vector(url: str) -> List[Any]:
    """Returns the 18 features in exact column order as a list for model inference."""
    feats_dict = extract_url_features(url)
    return [feats_dict[f] for f in DEPLOYABLE_URL_FEATURES]
