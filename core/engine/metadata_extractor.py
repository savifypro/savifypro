# core/engine/metadata_extractor.py

import os
import json
import threading
import uuid
import yt_dlp
import time
from pathlib import Path

from dir_setup import METADATA_DIR
from utils.file_extensions import AUDIO_FORMATS, VIDEO_FORMATS
from advanced.anti_blocker import GLOBAL_PROXY
from utils.cookie_loader import prepare_cookie_file
from utils.platform_detector import detect_platform, merge_headers_with_cookie
from utils.status_manager import update_status

PROCESS_CACHE = {}
_download_locks = {}

def _cache_path(url: str):
    safe = str(abs(hash(url)))
    return os.path.join(METADATA_DIR, f"{safe}.json")

def extract_metadata(url, headers=None, download_id=None):
    start = time.time()
    download_id = download_id or str(uuid.uuid4())

    if url in PROCESS_CACHE:
        result = PROCESS_CACHE[url].copy()
        result["download_id"] = download_id
        update_status(download_id, {"status": "ready", "cached": True})
        return result

    cache_file = _cache_path(url)
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cached = json.load(f)
            PROCESS_CACHE[url] = cached
            cached = cached.copy()
            cached["download_id"] = download_id
            update_status(download_id, {"status": "ready", "cached": True})
            return cached
        except:
            pass

    cancel_event = threading.Event()
    _download_locks[download_id] = cancel_event

    update_status(download_id, {"status": "extracting", "progress": 0})

    platform = detect_platform(url)
    merged_headers = merge_headers_with_cookie(headers or {}, platform)
    cookie_file = prepare_cookie_file(headers, platform)

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "simulate": True,
        "skip_download": True,
        "noplaylist": True,
        "extract_flat": False,
        "check_formats": False,
        "socket_timeout": 5,
        "extractor_retries": 1,
        "ignoreerrors": True,
        "lazy_playlist": True,
        "http_headers": merged_headers,
        "skip_unavailable_fragments": True,
        "concurrent_fragment_downloads": 1,
        "progress_hooks": [
            lambda _: cancel_event.is_set() and (_ for _ in ()).throw(Exception("Cancelled"))
        ],
        "extractor_args": {
            "youtube": {"skip": ["dash", "translated_subs", "hls"]},
            "tiktok": {"api_hostname": ["api16-normal-c-useast1a"]},
        },
    }

    if cookie_file:
        ydl_opts["cookiefile"] = cookie_file
    if GLOBAL_PROXY:
        ydl_opts["proxy"] = GLOBAL_PROXY

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as e:
        update_status(download_id, {"status": "error", "error": str(e)})
        return {"error": "Extraction failed", "download_id": download_id}

    if not info or "formats" not in info:
        update_status(download_id, {"status": "error", "error": "No metadata"})
        return {"error": "No metadata", "download_id": download_id}

    formats = info.get("formats") or []
    duration = info.get("duration") or 0

    audio_out = {}
    video_out = []
    seen_audio = set()
    seen_video = set()

    for f in formats:
        acodec = f.get("acodec")
        vcodec = f.get("vcodec")
        abr = f.get("abr")
        ext = f.get("ext")

        if vcodec == "none" and acodec != "none" and ext in AUDIO_FORMATS:
            if not abr:
                continue

            key = f"{int(abr)}K"
            if key in seen_audio:
                continue
            seen_audio.add(key)

            size = f.get("filesize") or f.get("filesize_approx")
            if not size and f.get("tbr") and duration:
                size = (f["tbr"] * 1000 / 8) * duration

            size_str = f"{round(size / 1024 / 1024, 2)}MB" if size else "Unknown"

            audio_out[key] = {
                "label": key,
                "abr": abr,
                "ext": ext,
                "format_id": f.get("format_id"),
                "size": size_str,
            }

    if not audio_out:
        for br in [256, 192, 128]:
            audio_out[f"{br}K"] = {
                "label": f"{br}K",
                "abr": br,
                "ext": "mp3",
                "format_id": f"fallback_{br}",
                "size": "Unknown",
            }

    for f in formats:
        height = f.get("height")
        vcodec = f.get("vcodec")
        ext = f.get("ext")

        if not height or vcodec == "none" or ext not in VIDEO_FORMATS:
            continue

        label = f"{height}p"
        if label in seen_video:
            continue
        seen_video.add(label)

        size = f.get("filesize") or f.get("filesize_approx")
        if not size and f.get("tbr") and duration:
            size = (f["tbr"] * 1000 / 8) * duration
        size_str = f"{round(size / 1024 / 1024, 2)}MB" if size else "Unknown"

        video_out.append({
            "label": label,
            "ext": ext,
            "size": size_str,
            "fps": f.get("fps"),
            "format_id": f.get("format_id"),
        })

    result = {
        "download_id": download_id,
        "platform": platform,
        "title": info.get("title"),
        "webpage_url": info.get("webpage_url"),
        "audioFormats": list(audio_out.values()),
        "videoFormats": video_out,
        "resolutions": [v["label"] for v in video_out],
        "sizes": [v["size"] for v in video_out],
        "url": url,
    }

    PROCESS_CACHE[url] = result.copy()
    Path(METADATA_DIR).mkdir(parents=True, exist_ok=True)
    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
    except:
        pass

    update_status(download_id, {"status": "ready"})
    return result
