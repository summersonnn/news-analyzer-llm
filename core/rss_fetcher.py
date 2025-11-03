import aiohttp

async def fetch_feed_content(session: aiohttp.ClientSession, url: str) -> bytes:
    """
    Fetch raw feed content from the given URL.
    Makes absolutely no assumptions about format, tags, or structure.
    It could be RSS, Atom, JSON Feed, or custom XML/HTML.
    """
    print(f"Fetching: {url}")
    async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
        resp.raise_for_status()
        return await resp.read()
