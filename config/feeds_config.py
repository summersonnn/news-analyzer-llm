from feeds.haberturk_feed import haberturk_postprocess
from feeds.techcrunch_feed import techcrunch_postprocess
from feeds.wired_feed import wired_postprocess
from feeds.arstechnica_feed import arstechnica_postprocess
from feeds.geekwire_feed import geekwire_postprocess
from feeds.theverge_feed import theverge_postprocess
from feeds.engadget_feed import engadget_postprocess

FEEDS = [
    {
        "name": "Haberturk",
        "urls": [
            "https://www.haberturk.com/rss/manset.xml",
            "https://www.haberturk.com/rss/ekonomi.xml",
        ],
        "postprocess_fn": haberturk_postprocess,
        "llm_prompt": (
            "Determine if this Turkish news article concerns an improvement or advancement in Turkey’s military capabilities — such as the introduction of new weapons, technologies like aircraft, drones, or defense systems. Focus only on concrete, measurable military developments, not political statements or rhetoric."
            "Score from 1–10, where 10 is highly related to AI."
        ),
    },
    {
        "name": "Tech Crunch",
        "urls": ["https://techcrunch.com/feed/"],
        "postprocess_fn": techcrunch_postprocess,
        "llm_prompt": (
            "Assess how strongly this article discusses a partnership, collaboration, or any type of relationship —positive or negative— between multiple companies."
            "Score 0–10 with a brief reasoning."
        ),
    },
    {
        "name": "Wired",
        "urls": [
            "https://www.wired.com/feed/category/business/latest/rss",
            "https://www.wired.com/feed/tag/ai/latest/rss",
        ],
        "postprocess_fn": wired_postprocess,
        "llm_prompt": (
            "Assess how strongly this article discusses a partnership, collaboration, or any type of relationship —positive or negative— between multiple companies."
            "Give a score (0–10) and short reasoning."
        ),
    },
    {
        "name": "Ars Technica",
        "urls": ["https://feeds.arstechnica.com/arstechnica/index"],
        "postprocess_fn": arstechnica_postprocess,
        "llm_prompt": (
            "Assess how strongly this article discusses a partnership, collaboration, or any type of relationship —positive or negative— between multiple companies."
            "Score 0–10 with reasoning."
        ),
    },
    {
        "name": "GeekWire",
        "urls": ["https://www.geekwire.com/feed/"],
        "postprocess_fn": geekwire_postprocess,
        "llm_prompt": (
            "Assess how strongly this article discusses a partnership, collaboration, or any type of relationship —positive or negative— between multiple companies."
            "Give a 0–10 relevance score."
        ),
    },

    {
        "name": "The Verge",
        "urls": ["https://www.theverge.com/rss/index.xml"],
        "postprocess_fn": theverge_postprocess,
        "llm_prompt": (
            "Assess how strongly this article discusses a partnership, collaboration, or any type of relationship —positive or negative— between multiple companies."
            "Score 0–10 with concise reasoning."
        ),
    },

    {
        "name": "Engadget",
        "urls": ["https://www.engadget.com/rss.xml"],
        "postprocess_fn": engadget_postprocess,
        "llm_prompt": (
            "Assess how strongly this article discusses a partnership, collaboration, or any type of relationship —positive or negative— between multiple companies."
            "Score 0–10 with concise reasoning."
        ),
    },
]
