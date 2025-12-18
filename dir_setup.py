# dir_setup.py

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VIDEO_DIR = os.path.join(BASE_DIR, "storage", "videos")
AUDIO_DIR = os.path.join(BASE_DIR, "storage", "audios")
METADATA_DIR = os.path.join(BASE_DIR, "cache")

os.makedirs(VIDEO_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(METADATA_DIR, exist_ok=True)
