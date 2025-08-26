import re
from urllib.parse import urlparse, parse_qs

_YT_ID_RE = re.compile(r"^[a-zA-Z0-9_-]{11}$")

def extract_youtube_id(url: str) -> str | None:
    # Accept full URLs or bare IDs
    if _YT_ID_RE.match(url):
        return url
    u = urlparse(url)
    if u.netloc.endswith(("youtube.com", "youtu.be")):
        if u.netloc.endswith("youtu.be"):
            return u.path.strip("/").split("/")[0] or None
        if u.path == "/watch":
            return parse_qs(u.query).get("v", [None])[0]
        # e.g. /embed/<id> or /shorts/<id>
        parts = [p for p in u.path.split("/") if p]
        return parts[-1] if parts else None
    return None