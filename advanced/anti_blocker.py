import os
import random
import time
from itertools import cycle

_raw_proxies = os.getenv("SAVIFYPRO_PROXIES", "")
PROXY_LIST = [p.strip() for p in _raw_proxies.split(",") if p.strip()]
PROXY_ROTATOR = cycle(PROXY_LIST) if PROXY_LIST else None
GLOBAL_PROXY = os.getenv("SAVIFYPRO_PROXY") or (PROXY_LIST[0] if PROXY_LIST else None)

def get_proxy(rotate=False, failover=True):
    proxy = next(PROXY_ROTATOR) if rotate and PROXY_ROTATOR else GLOBAL_PROXY
    if failover and not proxy_is_alive(proxy):
        return get_proxy(rotate=True, failover=False)
    return proxy

def proxy_is_alive(proxy):
    return bool(proxy)

USER_AGENT_FILE = os.path.join("advanced", "user_agents", "user-agents.txt")

def load_user_agents():
    agents = []
    try:
        if os.path.exists(USER_AGENT_FILE):
            with open(USER_AGENT_FILE, "r", encoding="utf-8") as f:
                agents = [line.strip() for line in f if line.strip()]
    except:
        pass
    if not agents:
        agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:110.0) Gecko/20100101 Firefox/110.0",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15A372 Safari/604.1",
            "Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_3_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
        ]
    return agents

USER_AGENTS = load_user_agents()

def get_random_user_agent():
    return random.choice(USER_AGENTS)

REFERER_POOL = [
    "https://www.google.com/",
    "https://www.bing.com/",
    "https://www.yahoo.com/",
    "https://twitter.com/",
    "https://www.facebook.com/",
    "https://www.youtube.com/",
]

def get_headers(platform=None):
    ua = get_random_user_agent()
    referer = random.choice(REFERER_POOL)
    headers = {
        "User-Agent": ua,
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": random.choice(["en-US,en;q=0.9", "en-GB,en;q=0.8"]),
        "Connection": "keep-alive",
        "Referer": referer,
        "DNT": str(random.choice([0, 1])),
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": random.choice(["document", "empty", "image", "script"]),
        "Sec-Fetch-Mode": random.choice(["navigate", "cors", "no-cors"]),
    }
    if platform == "tiktok":
        headers.update({
            "x-secsdk-csrf-token": "0001000000010001",
            "sec-ch-ua-platform": '"Android"',
        })
    elif platform == "youtube":
        headers["Referer"] = "https://www.youtube.com/"
        headers["Origin"] = "https://www.youtube.com"
    elif platform == "facebook":
        headers["Referer"] = "https://www.facebook.com/"
        headers["Origin"] = "https://www.facebook.com"
    return headers

def attach_proxy_to_ydl_opts(ydl_opts, rotate=False):
    proxy = get_proxy(rotate)
    if proxy:
        ydl_opts["proxy"] = proxy
    ydl_opts["http_headers"] = get_headers()
    return ydl_opts

def human_jitter(min_delay=0.1, max_delay=0.4):
    time.sleep(random.uniform(min_delay, max_delay))
