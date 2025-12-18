import os
import time
import shutil
from datetime import datetime

from dir_setup import AUDIO_DIR, METADATA_DIR, VIDEO_DIR


CLEAN_INTERVAL_SECONDS = 10 * 60  # 10 minutes

DIRS_TO_CLEAN = [
    VIDEO_DIR,
    AUDIO_DIR,
    METADATA_DIR,
]

# Ensure directories exist
for d in DIRS_TO_CLEAN:
    os.makedirs(d, exist_ok=True)


# ---------------- CLEAN LOGIC ----------------

def clean_directory(directory: str):
    """
    Deletes all files and folders inside a directory
    but keeps the root directory.
    """
    if not os.path.isdir(directory):
        return

    for item in os.listdir(directory):
        path = os.path.join(directory, item)
        try:
            if os.path.isfile(path) or os.path.islink(path):
                os.unlink(path)
            elif os.path.isdir(path):
                shutil.rmtree(path)
        except Exception as e:
            print(f"[✕] Failed to delete {path}: {e}")


def run_cleaner():
    print("[✓] Cleaner started. Running every 10 minutes...\n")

    while True:
        start = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[!] CLEAN START → {start}")

        for directory in DIRS_TO_CLEAN:
            print(f"    • Cleaning: {directory}")
            clean_directory(directory)

        end = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[✓] CLEAN DONE  → {end}\n")

        time.sleep(CLEAN_INTERVAL_SECONDS)


# ---------------- ENTRY ----------------

if __name__ == "__main__":
    try:
        run_cleaner()
    except KeyboardInterrupt:
        print("\n[!] Cleaner stopped manually.")
