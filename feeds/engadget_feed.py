# feeds/engadget_feed.py
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
import re
import html
import email.utils


def engadget_postprocess(raw_bytes):
    """
    Parse and standardize an Engadget RSS feed.
    Input: raw XML bytes
    Output: list of standardized dicts with keys:
        title, link, description, pub_date, pub_date_str, image
    """

    def clean_html(raw_html: str) -> str:
        """Strip tags and decode entities."""
        if not raw_html:
            return ""
        cleaned = re.sub(r"<iframe[^>]*>.*?</iframe>", " ", raw_html, flags=re.DOTALL | re.IGNORECASE)
        cleaned = re.sub(r"<core-commerce[^>]*>.*?</core-commerce>", " ", cleaned, flags=re.DOTALL | re.IGNORECASE)
        cleaned = re.sub(r"<[^>]+>", " ", cleaned)  # remove any remaining tags
        cleaned = html.unescape(cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned)
        return cleaned.strip()

    def normalize_text(text: str) -> str:
        """Normalize smart punctuation and whitespace."""
        text = html.unescape(text or "")
        text = text.strip()
        text = text.replace("\u2013", "-").replace("\u2014", "-")
        text = text.replace("\u2018", "'").replace("\u2019", "'")
        text = text.replace("\u201c", '"').replace("\u201d", '"')
        text = text.replace("\xa0", " ")
        text = re.sub(r"\s+", " ", text)
        return text

    # --- Parse XML ---
    xml_str = raw_bytes.decode("utf-8", errors="ignore")
    root = ET.fromstring(xml_str)
    items = []

    # Engadget uses standard RSS 2.0 <item> tags
    for node in root.findall(".//item"):
        title = normalize_text(node.findtext("title", ""))
        link = (node.findtext("link") or "").strip()
        description = clean_html(node.findtext("description", ""))
        pub_date_str = (node.findtext("pubDate") or "").strip()

        # --- Parse publication date robustly ---
        pub_date = None
        if pub_date_str:
            try:
                pub_date = email.utils.parsedate_to_datetime(pub_date_str)
                if pub_date.tzinfo is None:
                    pub_date = pub_date.replace(tzinfo=timezone.utc)
                else:
                    pub_date = pub_date.astimezone(timezone.utc)
            except Exception:
                for fmt in [
                    "%a, %d %b %Y %H:%M:%S %z",
                    "%a, %d %b %Y %H:%M:%S %Z",
                ]:
                    try:
                        pub_date = datetime.strptime(pub_date_str, fmt)
                        if pub_date.tzinfo is None:
                            pub_date = pub_date.replace(tzinfo=timezone.utc)
                        else:
                            pub_date = pub_date.astimezone(timezone.utc)
                        break
                    except Exception:
                        continue

        # --- Extract media image (if any) ---
        image_url = ""
        for media_tag in node.findall(".//{http://search.yahoo.com/mrss/}content"):
            url = media_tag.attrib.get("url")
            if url and url.strip():
                image_url = url.strip()
                break

        items.append({
            "title": title,
            "link": link,
            "description": description,
            "pub_date": pub_date,
            "pub_date_str": pub_date_str,
            "image": image_url,
        })

    return items
