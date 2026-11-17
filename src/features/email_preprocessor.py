"""
src/features/email_preprocessor.py
Standardized text preprocessing pipeline for email spam classification.
Production Version: Variant C (HTML-Aware + Controlled Footer Consolidation).
Replicates the exact normalization verified in Phase 5 and Phase 6 benchmarking.
"""

import re
import html
from typing import Optional


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


def preprocess_email_text(subject: Optional[str] = "", message: Optional[str] = "") -> str:
    """
    Production Preprocessor (Variant C: HTML-Aware + Controlled Footer Consolidation):
    1. Fill None with empty string.
    2. Clean HTML structure, delete <script>/<style> content, decode HTML entities.
    3. Apply controlled opt-out boilerplate consolidation.
    4. Concatenate subject + message.
    5. Lowercase.
    6. Strip embedded URLs (http://, https://, www.)
    7. Strip non-alphanumeric punctuation.
    8. Normalize and trim whitespace.
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
