# tools/cookie_loader.py

import tempfile
from utils.platform_detector import get_cookie_file_for_platform

TEMP_COOKIE_SUFFIX = "_cookie.txt"

def prepare_cookie_file(headers, platform):
    if headers and "Cookie" in headers:
        temp = tempfile.NamedTemporaryFile(delete=False, suffix=TEMP_COOKIE_SUFFIX, mode='w')
        temp.write(headers["Cookie"])
        temp.close()
        print(f"[!] INFO: Using header-based cookie file: {temp.name}")
        return temp.name

    fallback = get_cookie_file_for_platform(platform)
    if fallback:
        print(f"[!] INFO: Using fallback cookie file: {fallback}")
        return fallback

    print(f"[!] INFO: No cookie used for platform: {platform}")
    return None
