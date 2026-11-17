"""
backend/app/services/eml_parser.py
Robust RFC 822 / MIME .eml email file parser.
Extracts standard email headers and extracts body text from plain text and HTML payloads,
preserving embedded hyperlinks for downstream threat detection.
"""

import email
from email import policy
from dataclasses import dataclass
from typing import Optional
from bs4 import BeautifulSoup

@dataclass
class ParsedEML:
    subject: str
    sender: str
    recipient: str
    date: str
    message_id: str
    body_text: str

def parse_eml_bytes(file_bytes: bytes) -> ParsedEML:
    """
    Parses raw bytes from an uploaded .eml file.
    Extracts headers and normalizes multi-part MIME text/HTML payloads.
    """
    if not file_bytes or len(file_bytes.strip()) == 0:
        raise ValueError("The uploaded .eml file is empty.")

    try:
        msg = email.message_from_bytes(file_bytes, policy=policy.default)
    except Exception as e:
        raise ValueError(f"Failed to parse email structure: {str(e)}")

    subject = str(msg.get("Subject", "") or "").strip()
    sender = str(msg.get("From", "") or "").strip()
    recipient = str(msg.get("To", "") or "").strip()
    date_str = str(msg.get("Date", "") or "").strip()
    message_id = str(msg.get("Message-ID", "") or "").strip()

    body_chunks = []

    # If simple message
    if not msg.is_multipart():
        content_type = msg.get_content_type()
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            text = payload.decode(charset, errors="replace")
            if content_type == "text/html":
                text = _extract_text_and_links_from_html(text)
            body_chunks.append(text)
    else:
        # Walk multi-part components
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition", ""))
            
            # Skip file attachments
            if "attachment" in content_disposition:
                continue

            if content_type in ["text/plain", "text/html"]:
                payload = part.get_payload(decode=True)
                if not payload:
                    continue
                charset = part.get_content_charset() or "utf-8"
                text = payload.decode(charset, errors="replace")
                
                if content_type == "text/html":
                    text = _extract_text_and_links_from_html(text)
                
                body_chunks.append(text)

    combined_body = "\n".join(body_chunks).strip()
    
    # If no body was found in parts, fallback to str(msg)
    if not combined_body and not subject:
        # Check if the raw file has non-standard ascii text
        raw_text = file_bytes.decode("utf-8", errors="replace").strip()
        if raw_text:
            combined_body = raw_text

    return ParsedEML(
        subject=subject,
        sender=sender,
        recipient=recipient,
        date=date_str,
        message_id=message_id,
        body_text=combined_body
    )

def _extract_text_and_links_from_html(html_content: str) -> str:
    """Extracts text and ensures href targets are present in the text stream."""
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        # Ensure href targets in <a> tags are explicitly in the text so URL extractor catches them
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            a_text = a_tag.get_text()
            if href and href not in a_text:
                a_tag.append(f" {href} ")
        return soup.get_text(separator=" ", strip=True)
    except Exception:
        return html_content
