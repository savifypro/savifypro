import subprocess
from pathlib import Path
import shutil
import re
import random
from typing import Optional, Callable

# Configurations
try:
    from config.server_config import FINAL_IP, SERVER_URL
    from dir_setup import AUDIO_DIR, VIDEO_DIR
except ImportError:
    FINAL_IP = "http://localhost:8000"
    AUDIO_DIR, VIDEO_DIR = "downloads/audio", "downloads/video"

AUDIO_DIR, VIDEO_DIR = Path(AUDIO_DIR), Path(VIDEO_DIR)
for d in [AUDIO_DIR, VIDEO_DIR]: d.mkdir(parents=True, exist_ok=True)

LOGO_PATH = Path("utils/logo/logo.png")

def save_uploaded_file(upload_file) -> str:
    target_path = VIDEO_DIR / Path(upload_file.filename).name
    with open(target_path, "wb") as f:
        shutil.copyfileobj(upload_file.file, f)
    return str(target_path)

def convert_video_to_audio(
    input_path: str,
    out_format: str = "mp3",
    bitrate: str = "192k",
    progress_callback: Optional[Callable[[int], None]] = None
) -> str:
    input_file = Path(input_path)
    if not input_file.exists(): raise FileNotFoundError("Input missing")
    
    # Requirements: SoniEffect_Converted_Audio_<original filename>.mp3
    # Title: SoniEffect Converted Audio #<unique 3 digits>
    rand_3 = random.randint(100, 999)
    output_filename = f"SoniEffect_Converted_Audio_{input_file.stem}.{out_format}"
    out_path = AUDIO_DIR / output_filename
    
    # Metadata strings
    title_tag = f"SoniEffect Converted Audio #{rand_3}"
    artist_tag = "SoniEffect"

    # --- THE MILLISECOND ENGINE ---
    # -hwaccel auto: Uses GPU if available (Nvidia/Intel/Apple)
    # -thread_queue_size: Prevents buffer bottlenecks on large files
    # -preset ultrafast: Maximum speed algorithm
    cmd = [
        "ffmpeg", "-y",
        "-hwaccel", "auto",             # GPU Acceleration
        "-thread_queue_size", "1024",   # High-speed buffer
        "-i", str(input_file)
    ]

    has_logo = LOGO_PATH.exists()
    if has_logo:
        cmd.extend(["-i", str(LOGO_PATH)])

    # Optimization: Map audio only to avoid decoding heavy video pixels
    cmd.extend(["-map", "0:a"]) 
    
    if has_logo:
        cmd.extend(["-map", "1:v", "-disposition:v:0", "attached_pic"])

    # Codec Speed Settings
    if out_format == "mp3":
        cmd.extend([
            "-c:a", "libmp3lame",
            "-b:a", bitrate,
            "-preset", "ultrafast",
            "-id3v2_version", "3",
            "-metadata:s:v", "title=Album cover",
            "-metadata:s:v", "comment=Cover (front)"
        ])
    elif out_format == "m4a":
        cmd.extend(["-c:a", "aac", "-b:a", bitrate, "-preset", "ultrafast"])
    else:
        cmd.extend(["-c:a", "flac" if out_format == "flac" else "pcm_s16le"])

    # Global Tags
    cmd.extend([
        "-metadata", f"title={title_tag}",
        "-metadata", f"artist={artist_tag}",
        "-metadata", "album=SoniEffect Conversions",
        "-movflags", "+faststart",      # Enables instant playback/streaming
        str(out_path)
    ])

    # Execute with high-priority pipe
    process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
        text=True, bufsize=10**6 # 1MB buffer for speed
    )
    
    # Progress monitoring (Minimal overhead for speed)
    duration = None
    for line in process.stderr:
        if not duration:
            dur_match = re.search(r"Duration:\s(\d+):(\d+):(\d+\.\d+)", line)
            if dur_match:
                h, m, s = map(float, dur_match.groups())
                duration = h * 3600 + m * 60 + s
        elif progress_callback:
            time_match = re.search(r"time=(\d+):(\d+):(\d+\.\d+)", line)
            if time_match:
                h, m, s = map(float, time_match.groups())
                prog = min(int(((h*3600+m*60+s) / duration) * 100), 100)
                progress_callback(prog)

    process.wait()

    # Post-Conversion Cleanup (Non-blocking)
    try:
        input_file.unlink()
    except:
        pass

    print(f"\n[⚡] DESTROYED SPEEDS: {output_filename}")
    print(f"[↓] LINK: {SERVER_URL}/download/audio/{output_filename}")
    
    return str(out_path)

def delete_file(filename: str) -> bool:
    try:
        target = AUDIO_DIR / Path(filename).name
        if target.exists():
            target.unlink()
            return True
        return False
    except:
        return False
