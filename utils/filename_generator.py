import os
import re
from urllib.parse import quote, unquote
from dir_setup import VIDEO_DIR

def _normalize_basename_for_match(name: str) -> str:
    """Normalize filename for matching."""
    if not name:
        return ""
    name = unquote(name).lower()
    if name.endswith(".mp4"):
        name = name[:-4]
    name = re.sub(r"[^\w]+", "_", name)
    name = re.sub(r"_+", "_", name).strip("_")
    return name


def _find_existing_video_file(expected_filename: str) -> str | None:
    """Find existing video file matching the expected filename."""
    expected_norm = _normalize_basename_for_match(expected_filename)

    try:
        for f in os.listdir(VIDEO_DIR):
            if f.lower().endswith(".mp4"):
                f_norm = _normalize_basename_for_match(f)
                if f_norm == expected_norm:
                    return os.path.join(VIDEO_DIR, f)
        for f in os.listdir(VIDEO_DIR):
            if f.lower().endswith(".mp4"):
                f_norm = _normalize_basename_for_match(f)
                if expected_norm in f_norm or f_norm in expected_norm:
                    return os.path.join(VIDEO_DIR, f)
    except FileNotFoundError:
        return None
    return None

def generate_video_filename(title: str, resolution: str, for_url=False) -> str:
    if not title:
        title = "video"
    title = re.sub(r"[^\x00-\x7F]+", "", title)
    title = re.sub(r'[\\/*?:"<>|_%&+{}\[\]\$!`~^]', "", title)
    title = title.strip().replace(" ", "_")
    title = re.sub(r"_+", "_", title)
    title = title[:150]
    filename = f"{title}({resolution}).mp4"
    return quote(filename) if for_url else filename

def generate_audio_filename(title: str, for_url=False) -> str:
    if not title:
        title = "audio"
    title = re.sub(r"[^\x00-\x7F]+", "", title)
    title = re.sub(r'[\\/*?:"<>|_%&+{}\[\]\$!`~^]', "", title)
    title = title.strip().replace(" ", "_")
    title = re.sub(r"_+", "_", title)
    title = title[:150]
    return quote(title) if for_url else title
