import os
import re
import threading
import uuid
import yt_dlp  # type: ignore
import time
import traceback
from urllib.parse import quote

from advanced.anti_blocker import GLOBAL_PROXY
from config.server_config import SERVER_URL
from core.engine.progress_hook import _progress_hook
from dir_setup import AUDIO_DIR
from utils.cookie_loader import prepare_cookie_file
from utils.filename_generator import generate_audio_filename
from utils.platform_detector import detect_platform, merge_headers_with_cookie
from utils.status_manager import update_status

_download_threads = {}
_download_locks = {}

def start_audio_download(url: str, bitrate: str = "128kbps", headers: dict = None) -> str:
    """
    Starts an asynchronous audio download from a given URL.
    Returns a download_id which can be used to poll status.
    """
    download_id = str(uuid.uuid4())
    cancel_event = threading.Event()
    _download_locks[download_id] = cancel_event

    platform = detect_platform(url)

    def run():
        update_status(download_id, {
            "status": "starting",
            "progress": 0,
            "speed": "0KB/s",
            "audio_url": None
        })

        try:
            # Merge any provided headers with cookie-based headers for platform
            merged_headers = merge_headers_with_cookie(headers or {}, platform)
            cookie_file = prepare_cookie_file(headers, platform)

            # Attempt to get title for filename
            title = "audio"
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
            except Exception:
                # Ignore extract title failure
                pass

            safe_title_no_ext = generate_audio_filename(title)
            output_path_no_ext = os.path.join(AUDIO_DIR, safe_title_no_ext)

            outtmpl = f"{output_path_no_ext}.%(ext)s"
            expected_mp3_path = f"{output_path_no_ext}.mp3"

            # If already downloaded, skip
            existing_file = None
            for file in os.listdir(AUDIO_DIR):
                if file.lower().startswith(safe_title_no_ext.lower()) and file.lower().endswith(".mp3"):
                    existing_file = os.path.join(AUDIO_DIR, file)
                    break

            if existing_file and os.path.getsize(existing_file) > 0:
                audio_url = f"{SERVER_URL}/download/audio/{quote(os.path.basename(existing_file))}"
                update_status(download_id, {
                    "status": "completed",
                    "progress": 100,
                    "speed": "0KB/s",
                    "audio_url": audio_url
                })
                return

            # Determine preferred quality
            preferred_quality = re.sub(r"kbps?", "", bitrate, flags=re.IGNORECASE)

            concurrency = max(6, min(16, (os.cpu_count() or 4)))

            # Options for youtube + general
            ydl_opts = {
                "format": "bestaudio[ext=m4a]/bestaudio/best",
                "outtmpl": outtmpl,
                "noplaylist": True,
                "http_headers": merged_headers,
                "progress_hooks": [lambda d: _progress_hook(d, download_id, cancel_event)],
                "concurrent_fragment_downloads": concurrency,
                "continuedl": True,
                "retries": 10,
                "fragment_retries": 10,
                "socket_timeout": 60,
                "geo_bypass": True,
                "quiet": False,
                "noprogress": False,
                "no_warnings": True,
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": preferred_quality
                }],
                "postprocessor_args": [
                    "-movflags", "+faststart",
                    "-max_muxing_queue_size", "9999"
                ],
                # YouTube-specific extractor args to bypass SABR
                "extractor_args": {
                    "youtube": {
                        "player_client": ["android", "android_embedded"],
                        # optionally skip questionable clients
                        "skip": ["webpage", "web"],
                    }
                }
            }

            if cookie_file:
                ydl_opts["cookiefile"] = cookie_file
            if GLOBAL_PROXY:
                ydl_opts["proxy"] = GLOBAL_PROXY

            # Launch download
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            if cancel_event.is_set():
                update_status(download_id, {"status": "cancelled"})
                return

            # Find final mp3
            final_file = None
            for f in os.listdir(AUDIO_DIR):
                if f.lower().startswith(safe_title_no_ext.lower()) and f.lower().endswith(".mp3"):
                    final_file = os.path.join(AUDIO_DIR, f)
                    break

            if not final_file or os.path.getsize(final_file) == 0:
                raise FileNotFoundError("No MP3 output created.")

            audio_url = f"{SERVER_URL}/download/audio/{quote(os.path.basename(final_file))}"
            update_status(download_id, {
                "status": "completed",
                "progress": 100,
                "speed": "0KB/s",
                "audio_url": audio_url
            })

        except yt_dlp.utils.DownloadError as e:
            msg = str(e).lower()
            error_msg = (
                "Login or CAPTCHA required." if ("sign in" in msg or "captcha" in msg) else
                "Unsupported audio link." if "unsupported url" in msg else
                "Format unavailable or private content." if "requested format not available" in msg else
                "Audio download failed."
            )
            update_status(download_id, {"status": "error", "error": error_msg})

        except Exception:
            traceback.print_exc()
            update_status(download_id, {
                "status": "error",
                "error": "Unexpected error occurred while downloading."
            })

    thread = threading.Thread(target=run, daemon=True)
    _download_threads[download_id] = thread
    thread.start()
    return download_id
