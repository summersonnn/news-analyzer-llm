import xml.etree.ElementTree as ET
from datetime import datetime, timezone
import re
import html

def geekwire_postprocess(raw_bytes):
    """
    Parse and standardize a GeekWire RSS feed.
    Input: raw XML bytes
    Output: list of standardized dicts with title, link, description, pub_date, pub_date_str
    """

    def clean_html(raw_html: str) -> str:
        """Strip HTML tags, images, and decode entities."""
        if not raw_html:
            return ""
        cleaned = re.sub(r"<img[^>]*>", " ", raw_html, flags=re.IGNORECASE)
        cleaned = re.sub(r"</?a[^>]*>", " ", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"<br\s*/?>", " ", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"<[^>]+>", " ", cleaned)
        cleaned = html.unescape(cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned)
        return cleaned.strip()

    # --- Parse XML ---
    root = ET.fromstring(raw_bytes)
    items = []

    # GeekWire uses standard RSS 2.0 <item> tags
    for node in root.findall(".//item"):
        title = html.unescape((node.findtext("title") or "").strip())
        description = clean_html(node.findtext("description", ""))
        link = (node.findtext("link") or "").strip()
        pub_date_str = (node.findtext("pubDate") or "").strip()

        # --- Parse date ---
        parsed = None
        for fmt in [
            "%a, %d %b %Y %H:%M:%S %z",
            "%a, %d %b %Y %H:%M:%S %Z",
        ]:
            try:
                parsed = datetime.strptime(pub_date_str, fmt)
                break
            except Exception:
                continue

        if parsed:
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            else:
                parsed = parsed.astimezone(timezone.utc)

        items.append({
            "title": title,
            "link": link,
            "description": description,
            "pub_date": parsed,
            "pub_date_str": pub_date_str,
        })

    return items
