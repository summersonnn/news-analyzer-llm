import xml.etree.ElementTree as ET
from datetime import datetime, timezone
import re

def wired_postprocess(raw_bytes):
    """
    Parse and standardize a WIRED RSS feed.
    Input: raw XML bytes
    Output: list of standardized dicts with title, link, description, pub_date, pub_date_str.
    """

    def normalize_text(text: str) -> str:
        """Normalize smart punctuation and whitespace."""
        text = (text or "").strip()
        text = text.replace("\u2013", "-").replace("\u2014", "-")
        text = text.replace("\u2018", "'").replace("\u2019", "'")
        text = text.replace("\u201c", '"').replace("\u201d", '"')
        text = text.replace("\xa0", " ")  # remove non-breaking spaces
        text = re.sub(r"\s+", " ", text)
        return text

    # --- Parse XML ---
    root = ET.fromstring(raw_bytes)
    items = []

    # WIRED uses standard RSS 2.0 <item> tags
    for node in root.findall(".//item"):
        title = normalize_text(node.findtext("title", ""))
        link = (node.findtext("link") or "").strip()
        description = normalize_text(node.findtext("description", ""))
        pub_date_str = (node.findtext("pubDate") or "").strip()

        # --- Parse publication date ---
        parsed = None
        for fmt in [
            "%a, %d %b %Y %H:%M:%S %Z",  # e.g. Fri, 31 Oct 2025 18:34:14 GMT
            "%a, %d %b %Y %H:%M:%S %z",  # e.g. Fri, 31 Oct 2025 18:34:14 +0000
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
