import xml.etree.ElementTree as ET
from datetime import datetime, timezone

def techcrunch_postprocess(raw_bytes):
    """
    Parse and standardize the TechCrunch RSS feed.
    Input: raw XML bytes
    Output: list of standardized dicts with title, link, description, pub_date, pub_date_str
    """
    root = ET.fromstring(raw_bytes)
    items = []

    # TechCrunch uses standard RSS 2.0 <item> elements
    for node in root.findall(".//item"):
        title = (node.findtext("title") or "").strip()
        link = (node.findtext("link") or "").strip()
        description = (node.findtext("description") or "").strip()
        pub_date_str = (node.findtext("pubDate") or "").strip()

        # Parse pub_date
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
