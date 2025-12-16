import os
import re
from typing import Optional

def detect_platform(url: str) -> str:
    url = url.lower().strip()
    patterns = {
        "youtube": r"(youtube\.com|youtu\.be)",
        "facebook": r"(facebook\.com|fb\.watch)",
        "instagram": r"(instagram\.com|instagr\.am)",
        "tiktok": r"(tiktok\.com)",
        "twitter": r"(twitter\.com|x\.com)",
        "threads": r"(threads\.net)",
        "reddit": r"(reddit\.com)",
        "linkedin": r"(linkedin\.com)",
        "vimeo": r"(vimeo\.com)",
        "twitch": r"(twitch\.tv)",
        "soundcloud": r"(soundcloud\.com)",
        "dailymotion": r"(dailymotion\.com|dai\.ly)",
        "pinterest": r"(pinterest\.com|pin\.it)",
        "likee": r"(likee\.video)",
        "bilibili": r"(bilibili\.com|b23\.tv)",
        "vk": r"(vk\.com)",
        "rumble": r"(rumble\.com)",
        "odysee": r"(odysee\.com)",
        "pornhub": r"(pornhub\.com)",
        "xvideos": r"(xvideos\.com)",
        "redtube": r"(redtube\.com)",
        "youporn": r"(youporn\.com)",
        "xnxx": r"(xnxx\.com)",
        "metacafe": r"(metacafe\.com)",
        "liveleak": r"(liveleak\.com)",
        "9gag": r"(9gag\.com)",
        "xhamster": r"(xhamster\.com)",
        "bongacams": r"(bongacams\.com)",
        "chaturbate": r"(chaturbate\.com)",
        "coub": r"(coub\.com)",
        "mixcloud": r"(mixcloud\.com)",
        "bandcamp": r"(bandcamp\.com)",
        "hearthisat": r"(hearthisat\.com)",
    }
    for platform, pattern in patterns.items():
        if re.search(pattern, url):
            return platform
    return "unknown"


COOKIE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "cookies"))

FILENAME_MAP = {
    "youtube": "yt_cookies.txt",
    "facebook": "fb_cookies.txt",
    "instagram": "ig_cookies.txt",
    "tiktok": "tt_cookies.txt",
    "twitter": "tw_cookies.txt",
    "threads": "threads_cookies.txt",
    "reddit": "reddit_cookies.txt",
    "linkedin": "linkedin_cookies.txt",
    "vimeo": "vimeo_cookies.txt",
    "twitch": "twitch_cookies.txt",
    "soundcloud": "sc_cookies.txt",
    "dailymotion": "dm_cookies.txt",
    "pinterest": "pin_cookies.txt",
    "likee": "likee_cookies.txt",
    "bilibili": "bili_cookies.txt",
    "vk": "vk_cookies.txt",
    "rumble": "rumble_cookies.txt",
    "odysee": "odysee_cookies.txt",
}


def get_cookie_file_for_platform(platform: str) -> Optional[str]:
    fname = FILENAME_MAP.get(platform)
    if not fname:
        return None
    path = os.path.join(COOKIE_DIR, fname)
    return path if os.path.isfile(path) else None


def merge_headers_with_cookie(headers: dict, platform: str) -> dict:
    merged = headers.copy() if headers else {}
    if "Cookie" in merged:
        return merged
    cookie_path = get_cookie_file_for_platform(platform)
    if cookie_path:
        try:
            with open(cookie_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    merged["Cookie"] = content
        except Exception:
            pass
    return merged
