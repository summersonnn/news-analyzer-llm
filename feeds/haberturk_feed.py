import xml.etree.ElementTree as ET
from html import unescape
from datetime import datetime, timezone
import email.utils

def haberturk_postprocess(xml_bytes):
    """Parse Haberturk RSS feed (manset, ekonomi, etc.) and normalize entries."""
    xml_str = xml_bytes.decode("utf-8", errors="ignore")
    root = ET.fromstring(xml_str)

    channel = root.find("channel") or root
    entries = channel.findall("item")
    if not entries:
        # fallback: detect most frequent child tag
        children = list(channel)
        tag_counts = {}
        for c in children:
            tag_counts[c.tag] = tag_counts.get(c.tag, 0) + 1
        if tag_counts:
            top_tag = max(tag_counts.items(), key=lambda x: x[1])[0]
            entries = channel.findall(top_tag)

    results = []
    for e in entries:
        def get_text(*names):
            for n in names:
                node = e.find(n)
                if node is not None and node.text:
                    return node.text.strip()
            return ""

        title = unescape(get_text("title", "headline", "name"))
        link = get_text("link", "url", "guid")
        desc = unescape(get_text("description", "summary", "content", "subtitle"))
        pub_date_str = get_text("pubDate", "published", "updated", "date")

        # --- Parse pub_date robustly ---
        pub_date = None
        if pub_date_str:
            pub_date_str = pub_date_str.strip().replace("\xa0", " ")
            try:
                pub_date = email.utils.parsedate_to_datetime(pub_date_str)
                if pub_date and pub_date.tzinfo is None:
                    pub_date = pub_date.replace(tzinfo=timezone.utc)
                elif pub_date:
                    pub_date = pub_date.astimezone(timezone.utc)
            except Exception:
                try:
                    # Handle "+03:00" or "+0300" manually if needed
                    fixed = pub_date_str.replace(" +03:00", " +0300")
                    pub_date = datetime.strptime(fixed, "%a, %d %b %Y %H:%M:%S %z").astimezone(timezone.utc)
                except Exception:
                    pub_date = None

        # --- Extract image ---
        img = ""
        for t in [
            "image",
            "{http://search.yahoo.com/mrss/}content",
            "{http://search.yahoo.com/mrss/}thumbnail",
            "enclosure",
        ]:
            node = e.find(t)
            if node is not None:
                img = node.attrib.get("url") or (node.text or "").strip()
                if img:
                    break

        results.append({
            "title": title,
            "link": link,
            "description": desc,
            "pub_date_str": pub_date_str,
            "pub_date": pub_date,
            "image": img,
        })

    return results
