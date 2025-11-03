import xml.etree.ElementTree as ET
from datetime import datetime, timezone
import re

def theverge_postprocess(raw_bytes):
    """
    Parse and standardize The Verge Atom feed.
    Input: raw XML bytes
    Output: list of standardized dicts with keys:
        title, link, author, summary, pub_date, pub_date_str
    """

    def normalize_text(text: str) -> str:
        """Clean up smart quotes, unicode dashes, etc."""
        text = (text or "").strip()
        text = text.replace("\u2013", "-").replace("\u2014", "-")
        text = text.replace("\u2018", "'").replace("\u2019", "'")
        text = text.replace("\u201c", '"').replace("\u201d", '"')
        text = text.replace("\xa0", " ")
        text = re.sub(r"\s+", " ", text)
        return text

    # Parse XML and detect Atom namespace if present
    root = ET.fromstring(raw_bytes)
    ns = {}
    if root.tag.startswith("{"):
        ns_uri = root.tag.split("}")[0].strip("{")
        ns["a"] = ns_uri  # Atom namespace alias

    items = []

    # Iterate over all <entry> nodes (Atom equivalent of <item>)
    for entry in root.findall(".//a:entry", ns) or root.findall(".//entry"):
        title = normalize_text(entry.findtext("a:title", default="", namespaces=ns))
        if not title:
            title = normalize_text(entry.findtext("title", default=""))

        # <link> in Atom may have attributes instead of text content
        link = ""
        link_el = entry.find("a:link", ns) or entry.find("link")
        if link_el is not None:
            link = link_el.attrib.get("href", "").strip()

        author_el = entry.find("a:author/a:name", ns) or entry.find("author/name")
        author = normalize_text(author_el.text if author_el is not None else "")

        summary = normalize_text(entry.findtext("a:summary", default="", namespaces=ns))
        if not summary:
            summary = normalize_text(entry.findtext("summary", default=""))

        # Prefer <published>, fallback to <updated>
        pub_date_str = (
            entry.findtext("a:published", default="", namespaces=ns)
            or entry.findtext("a:updated", default="", namespaces=ns)
            or entry.findtext("published", default="")
            or entry.findtext("updated", default="")
        ).strip()

        parsed = None
        if pub_date_str:
            try:
                parsed = datetime.fromisoformat(pub_date_str.replace("Z", "+00:00"))
                parsed = parsed.astimezone(timezone.utc)
            except Exception:
                parsed = None

        items.append({
            "title": title,
            "link": link,
            "author": author,
            "description": summary,
            "pub_date": parsed,
            "pub_date_str": pub_date_str,
        })

    return items
