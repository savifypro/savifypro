import subprocess
from pathlib import Path
import shutil
import re

from config.server_config import SERVER_URL
from dir_setup import AUDIO_DIR, VIDEO_DIR


# -------------------------------------------------
# ENSURE PATH OBJECTS (CRITICAL FIX)
# -------------------------------------------------
AUDIO_DIR = Path(AUDIO_DIR)
VIDEO_DIR = Path(VIDEO_DIR)

AUDIO_DIR.mkdir(parents=True, exist_ok=True)
VIDEO_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------- AUDIO CODECS ----------------------
AUDIO_CODECS = {
    "mp3": "libmp3lame",
    "wav": "pcm_s16le",
    "m4a": "aac",
    "flac": "flac",
    "ogg": "libvorbis",
}


# ---------------------- SAVE FILE ----------------------
def save_uploaded_file(upload_file) -> str:
    """
    Save uploaded video file safely.
    """
    original_filename = Path(upload_file.filename).name
    target_path = VIDEO_DIR / original_filename

    if target_path.exists():
        target_path.unlink()

    with open(target_path, "wb") as f:
        shutil.copyfileobj(upload_file.file, f)

    return str(target_path)


# ---------------------- CONVERT VIDEO ----------------------
def convert_video_to_audio(
    input_path: str,
    out_format: str = "mp3",
    bitrate: str = "192k"
) -> str:
    """
    Convert video to audio using FFmpeg with progress tracking.
    """

    try:
        input_file = Path(input_path)

        if not input_file.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")

        if out_format not in AUDIO_CODECS:
            raise ValueError(f"Unsupported audio format: {out_format}")

        codec = AUDIO_CODECS[out_format]
        output_file = f"{input_file.stem}.{out_format}"
        out_path = AUDIO_DIR / output_file

        print(f"[!] INFO: Starting conversion → {output_file}")

        cmd = [
            "ffmpeg",
            "-y",
            "-i", str(input_file),
            "-vn",
            "-acodec", codec,
            "-b:a", bitrate,
            str(out_path)
        ]

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

        duration = None

        for line in process.stderr:
            # Parse duration
            if duration is None:
                dur = re.search(r"Duration:\s(\d+):(\d+):(\d+\.\d+)", line)
                if dur:
                    h, m, s = map(float, dur.groups())
                    duration = h * 3600 + m * 60 + s

            # Parse progress time
            time_match = re.search(r"time=(\d+):(\d+):(\d+\.\d+)", line)
            if time_match and duration:
                h, m, s = map(float, time_match.groups())
                current = h * 3600 + m * 60 + s
                progress = min(int((current / duration) * 100), 100)
                print(f"[!] INFO: Converting... {progress}%", end="\r")

        process.wait()

        if process.returncode != 0:
            raise RuntimeError("FFmpeg failed to convert file")

        if not out_path.exists():
            raise RuntimeError("Output file not created")

        print(f"\n[✓] DONE: Conversion completed → {out_path.name}")
        print(f"[↓] DOWNLOAD: {SERVER_URL}/download/audio/{output_file}")

        return str(out_path)

    except Exception as e:
        print(f"[✕] ERROR: Conversion error → {e}")
        raise


# ---------------------- DELETE FILE ----------------------
def delete_file(filename: str) -> bool:
    """
    Delete converted audio file.
    """
    try:
        target = AUDIO_DIR / Path(filename).name

        if target.exists():
            target.unlink()
            print(f"[✓] DONE: Deleted file {filename}")
            return True

        print(f"[!] WARNING: File not found → {filename}")
        return False

    except Exception as e:
        print(f"[✕] ERROR: Delete failed → {e}")
        return False
