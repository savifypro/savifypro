import os
import re
import threading
from urllib.parse import quote
import uuid
import yt_dlp  # type: ignore
import traceback
import time

from advanced.anti_blocker import GLOBAL_PROXY
from config.server_config import SERVER_URL
from core.engine.progress_hook import _progress_hook
from dir_setup import VIDEO_DIR
from utils.cookie_loader import prepare_cookie_file
from utils.filename_generator import _find_existing_video_file, generate_video_filename
from utils.platform_detector import detect_platform, merge_headers_with_cookie
from utils.status_manager import update_status

_download_threads = {}
_download_locks = {}

def start_download(url, resolution, bandwidth_limit=None, headers=None, audio_lang=None):
    def parse_bandwidth_limit(limit):
        try:
            if not limit:
                return None
            if isinstance(limit, (int, float)):
                return int(float(limit) * 1024)
            s = str(limit).strip().upper()
            m = {'K': 1024, 'M': 1024 ** 2, 'G': 1024 ** 3}
            for u, mul in m.items():
                if s.endswith(u):
                    return int(float(s[:-1]) * mul)
            return int(float(s))
        except:
            return None

    download_id = str(uuid.uuid4())
    platform = detect_platform(url)
    cancel_event = threading.Event()
    _download_locks[download_id] = cancel_event

    def run():
        update_status(download_id, {"status": "starting", "progress": 0, "speed": "0KB/s", "video_url": None})

        try:
            merged_headers = merge_headers_with_cookie(headers or {}, platform)
            cookie_file = prepare_cookie_file(headers, platform)

            title = "video"
            try:
                with yt_dlp.YoutubeDL({
                    "quiet": True,
                    "skip_download": True,
                    "http_headers": merged_headers,
                    "cookiefile": cookie_file if cookie_file else None
                }) as ydl:
                    info = ydl.extract_info(url, download=False)
                    if isinstance(info, dict) and info.get("title"):
                        title = info["title"]
            except:
                pass

            expected_filename = generate_video_filename(title, resolution)
            expected_path = os.path.join(VIDEO_DIR, expected_filename)

            if os.path.exists(expected_path) and os.path.getsize(expected_path) > 0:
                video_url = f"{SERVER_URL}/download/video/{quote(os.path.basename(expected_path), safe='')}"
                update_status(download_id, {"status": "completed", "progress": 99, "speed": "0KB/s", "video_url": video_url})
                return

            matched = _find_existing_video_file(expected_filename)
            if matched and os.path.getsize(matched) > 0:
                video_url = f"{SERVER_URL}/download/video/{quote(os.path.basename(matched), safe='')}"
                update_status(download_id, {"status": "completed", "progress": 99, "speed": "0KB/s", "video_url": video_url})
                return

            height = re.sub(r"[^0-9]", "", resolution) or "1080"
            video_fmt = f"bestvideo[ext=mp4][height={height}]"
            audio_fmt = "bestaudio[ext=m4a]"
            if audio_lang:
                audio_fmt += f"[language^{audio_lang}]"
            format_selector = f"{video_fmt}+{audio_fmt}/best[ext=mp4][height<={height}]/best"

            concurrency = max(8, min(32, (os.cpu_count() or 4) * 2))
            rate_limit = parse_bandwidth_limit(bandwidth_limit)

            ydl_opts = {
                "format": format_selector,
                "outtmpl": expected_path,
                "quiet": True,
                "noplaylist": True,
                "merge_output_format": "mp4",
                "http_headers": merged_headers,
                "progress_hooks": [lambda d: _progress_hook(d, download_id, cancel_event)],
                "postprocessors": [
                    {"key": "FFmpegVideoConvertor", "preferedformat": "mp4"}
                ],
                "postprocessor_args": ["-movflags", "+faststart", "-max_muxing_queue_size", "9999"],
                "concurrent_fragment_downloads": concurrency,
                "http_chunk_size": 10 * 1024 * 1024,
                "nopart": True,
                "noresizebuffer": True,
                "buffersize": 32 * 1024 * 1024,
                "retries": 10,
                "fragment_retries": 10,
                "socket_timeout": 60,
                "throttledratelimit": 0,
                "continuedl": True,
                "noprogress": True,
                "overwrites": True,
            }

            if cookie_file:
                ydl_opts["cookiefile"] = cookie_file
            if rate_limit:
                ydl_opts["ratelimit"] = rate_limit
            if GLOBAL_PROXY:
                ydl_opts["proxy"] = GLOBAL_PROXY

            start_time = time.time()
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            elapsed = round(time.time() - start_time, 2)

            if cancel_event.is_set():
                update_status(download_id, {"status": "cancelled"})
                return

            if not os.path.exists(expected_path) or os.path.getsize(expected_path) == 0:
                raise FileNotFoundError("Output file missing after download.")

            video_url = f"{SERVER_URL}/download/video/{quote(os.path.basename(expected_path), safe='')}"
            update_status(download_id, {"status": "completed", "progress": 99, "speed": "0KB/s", "video_url": video_url})

        except yt_dlp.utils.DownloadError as e:
            msg = str(e).lower()
            error_msg = (
                "Login or CAPTCHA required." if ("sign in" in msg or "captcha" in msg) else
                "Unsupported or invalid video link." if "unsupported url" in msg else
                "Format not available or private video." if "requested format not available" in msg else
                "Download failed."
            )
            update_status(download_id, {"status": "error", "error": error_msg})
        except Exception:
            traceback.print_exc()
            update_status(download_id, {"status": "error", "error": "Unexpected error occurred while downloading."})

    thread = threading.Thread(target=run, daemon=True)
    _download_threads[download_id] = thread
    thread.start()
    return download_id
