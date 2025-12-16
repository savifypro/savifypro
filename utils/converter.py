import subprocess
from pathlib import Path
import shutil
import re

# ---------------------- DIRECTORIES ----------------------
BASE_INPUT_DIR = Path("data")
BASE_OUTPUT_DIR = Path("data/audio")
BASE_INPUT_DIR.mkdir(parents=True, exist_ok=True)
BASE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

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
    Save uploaded file without printing upload logs.
    """
    original_filename = Path(upload_file.filename).name
    target_path = BASE_INPUT_DIR / original_filename

    # Replace if exists
    if target_path.exists():
        target_path.unlink()

    # Save file
    with open(target_path, "wb") as f:
        shutil.copyfileobj(upload_file.file, f)

    return str(target_path)

# ---------------------- CONVERT VIDEO ----------------------
def convert_video_to_audio(input_path: str, out_format="mp3", bitrate="192k", final_ip="localhost") -> str:
    """
    Convert video file to audio using ffmpeg.
    Shows live progress as [!] INFO: Converting... xx%
    """
    try:
        input_file = Path(input_path)
        if not input_file.exists():
            raise FileNotFoundError(f"Input file does not exist: {input_file}")

        if out_format not in AUDIO_CODECS:
            raise ValueError(f"Unsupported audio format: {out_format}")

        output_file = f"{input_file.stem}.{out_format}"
        out_path = BASE_OUTPUT_DIR / output_file
        codec = AUDIO_CODECS[out_format]

        print(f"[!] INFO: Starting conversion to {out_format} ...")

        # ffmpeg command with progress info
        cmd = [
            "ffmpeg",
            "-y",
            "-i", str(input_file),
            "-vn",
            "-acodec", codec,
            "-b:a", bitrate,
            str(out_path)
        ]

        # Run ffmpeg with live stderr capture
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)

        duration = None
        for line in process.stderr:
            # Capture duration
            if duration is None:
                dur_match = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", line)
                if dur_match:
                    hours, minutes, seconds = map(float, dur_match.groups())
                    duration = hours * 3600 + minutes * 60 + seconds

            # Capture current time to calculate progress
            time_match = re.search(r"time=(\d+):(\d+):(\d+\.\d+)", line)
            if time_match and duration:
                h, m, s = map(float, time_match.groups())
                current_time = h * 3600 + m * 60 + s
                progress = int(current_time / duration * 100)
                print(f"[!] INFO: Converting... {progress}%", end="\r")

        process.wait()

        if process.returncode != 0:
            print(f"\n[✕] ERROR: FFmpeg conversion failed")
            raise RuntimeError("FFmpeg failed")

        if not out_path.exists():
            raise RuntimeError("Conversion failed: output file not found.")

        print(f"\n[✓] DONE: Conversion completed: {out_path.name}")
        print(f"[!] WARNING: Audio file is temporarily available at {final_ip}/api/download/{output_file}")

        return str(out_path)

    except Exception as e:
        print(f"[✕] ERROR: Conversion error: {e}")
        raise

# ---------------------- DELETE FILE ----------------------
def delete_file(filename: str) -> bool:
    """
    Delete audio file by name.
    Prints progress messages.
    """
    try:
        target = BASE_OUTPUT_DIR / Path(filename).name
        if target.exists():
            target.unlink()
            print(f"[✓] DONE: Deleted file {filename}")
            return True
        else:
            print(f"[!] WARNING: File not found: {filename}")
            return False
    except Exception as e:
        print(f"[✕] ERROR: Failed to delete file {filename}: {e}")
        return False
