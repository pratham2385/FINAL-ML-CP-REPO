"""
src/features/experimental_preprocessors.py
Phase 5: Experimental Preprocessing Variants for Legitimate Newsletter Recognition
Provides:
- Variant A: Current Baseline
- Variant B: HTML-Aware Preprocessor (handles style/script, entities, block tags)
- Variant C: HTML-Aware + Controlled Footer-Aware Preprocessor
- Variant D: Header/Body Structural Representation
"""

import re
import html
from typing import Optional, Tuple


def preprocess_variant_a(subject: Optional[str] = "", message: Optional[str] = "") -> str:
    """Variant A: Current production baseline unchanged."""
    subj = subject if isinstance(subject, str) else ""
    body = message if isinstance(message, str) else ""
    combined = f"{subj} {body}".strip()

    if not combined:
        return ""

    text = combined.lower()
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'http[s]?://\S+|www\.\S+', ' ', text)
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def clean_html_structure(raw_text: str) -> str:
    """Removes scripts, styles, comments, converts block tags to spaces, and unescapes entities."""
    if not raw_text:
        return ""

    # 1. Remove script and style elements completely including their contents
    text = re.sub(r'<script[^>]*>.*?</script>', ' ', raw_text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', ' ', text, flags=re.DOTALL | re.IGNORECASE)

    # 2. Remove HTML comments
    text = re.sub(r'<!--.*?-->', ' ', text, flags=re.DOTALL)

    # 3. Replace common HTML block-ending tags with a space so words don't merge
    text = re.sub(r'<(?:br|p|div|tr|td|li|h[1-6])[^>]*>', ' ', text, flags=re.IGNORECASE)
    text = re.sub(r'</(?:p|div|tr|td|li|h[1-6])>', ' ', text, flags=re.IGNORECASE)

    # 4. Strip remaining HTML tags
    text = re.sub(r'<[^>]+>', ' ', text)

    # 5. Decode HTML entities (&nbsp; -> space, &amp; -> &, &quot; -> ", etc.)
    text = html.unescape(text)

    return text


def preprocess_variant_b(subject: Optional[str] = "", message: Optional[str] = "") -> str:
    """
    Variant B: HTML-Aware Preprocessor.
    Decodes HTML entities, removes script/style blocks, cleans tags, strips URLs,
    normalizes punctuation and whitespace.
    """
    subj = subject if isinstance(subject, str) else ""
    body = message if isinstance(message, str) else ""

    subj_clean = clean_html_structure(subj)
    body_clean = clean_html_structure(body)

    combined = f"{subj_clean} {body_clean}".strip()
    if not combined:
        return ""

    text = combined.lower()
    # Strip URLs
    text = re.sub(r'http[s]?://\S+|www\.\S+', ' ', text)
    # Strip non-alphanumeric punctuation
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def preprocess_variant_c(subject: Optional[str] = "", message: Optional[str] = "") -> str:
    """
    Variant C: HTML-Aware + Controlled Footer-Aware Preprocessor.
    Applies Variant B cleaning, then identifies repetitive newsletter opt-out
    and legal boilerplate phrases and consolidates them into a canonical token
    rather than letting repetitive legal text dominate the bag-of-words.
    """
    subj = subject if isinstance(subject, str) else ""
    body = message if isinstance(message, str) else ""

    subj_clean = clean_html_structure(subj)
    body_clean = clean_html_structure(body)

    # Controlled footer boilerplate consolidation on body
    footer_patterns = [
        r'(?:to\s+unsubscribe|if\s+you\s+wish\s+to\s+unsubscribe|click\s+here\s+to\s+unsubscribe)[^.\n]{0,100}',
        r'you\s+received\s+this\s+email\s+because\s+you\s+subscribed[^.\n]{0,100}',
        r'to\s+be\s+removed\s+from\s+this\s+mailing\s+list[^.\n]{0,100}',
        r'all\s+rights\s+reserved\s+copyright\s+\d{4}[^.\n]{0,50}',
        r'manage\s+your\s+subscription\s+preferences[^.\n]{0,100}',
        r'privacy\s+policy\s+terms\s+of\s+service[^.\n]{0,100}',
    ]

    body_footer_processed = body_clean
    for pat in footer_patterns:
        body_footer_processed = re.sub(pat, ' newsletter_optout_boilerplate ', body_footer_processed, flags=re.IGNORECASE)

    combined = f"{subj_clean} {body_footer_processed}".strip()
    if not combined:
        return ""

    text = combined.lower()
    text = re.sub(r'http[s]?://\S+|www\.\S+', ' ', text)
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def preprocess_variant_d(subject: Optional[str] = "", message: Optional[str] = "") -> str:
    """
    Variant D: Structural Header/Body Representation.
    Prefixes subject tokens with 'subj_' to separate subject intent from body text.
    Tags mailing list identifiers if detected.
    """
    subj = subject if isinstance(subject, str) else ""
    body = message if isinstance(message, str) else ""

    # Check for mailing list tags in subject before cleaning
    is_mailing_list = bool(re.search(r'\[[a-zA-Z0-9_\-]+\]', subj))

    subj_clean = clean_html_structure(subj).lower()
    body_clean = clean_html_structure(body).lower()

    # URL stripping
    subj_clean = re.sub(r'http[s]?://\S+|www\.\S+', ' ', subj_clean)
    body_clean = re.sub(r'http[s]?://\S+|www\.\S+', ' ', body_clean)

    # Punctuation stripping
    subj_clean = re.sub(r'[^a-z0-9\s]', ' ', subj_clean)
    body_clean = re.sub(r'[^a-z0-9\s]', ' ', body_clean)

    # Prefix subject tokens
    subj_tokens = [f"subj_{w}" for w in subj_clean.split()]
    body_tokens = body_clean.split()

    extra_tokens = ["__mailing_list_tag__"] if is_mailing_list else []

    all_tokens = subj_tokens + extra_tokens + body_tokens
    return " ".join(all_tokens).strip()
