# tools/status_manager.py

import os
import copy
from threading import Lock
from time import time

_status_map = {}
_timestamp_map = {}
_lock = Lock()

DEFAULT_STATUS = {
    "status": "pending",           # pending, extracting, downloading, converting, completed, error, canceled
    "progress": 0.0,               # percentage progress
    "speed": "0KB/s",              # human-readable speed
    "eta": None,                   # estimated time remaining
    "downloaded": 0,               # bytes downloaded
    "total": 0,                    # total size in bytes
    "video_url": None,
    "platform": None,
    "phase": None,                 # finer-grained phase indicator
    "message": None,
    "error": None,
    "timestamp": 0,
    "created_at": 0,
    "completed_at": None,
    "file_type": "video",          # video, audio, playlist, etc.
    "filename": None,
    "filesize": None,
    "mimetype": None,
    "codec": None,
    "retries": 0,                  # how many times retried
    "history": []                  # log of status changes
}

MIN_VALID_FILESIZE = 512 * 1024  # 512KB minimum valid file

def _ensure_initialized(download_id: str):
    if download_id not in _status_map:
        now = int(time())
        _status_map[download_id] = copy.deepcopy(DEFAULT_STATUS)
        _status_map[download_id]["created_at"] = now
        _timestamp_map[download_id] = now

def _log_history(download_id: str, event: str, extra: dict = None):
    if download_id not in _status_map:
        return
    entry = {
        "time": int(time()),
        "event": event,
        **(extra or {})
    }
    _status_map[download_id]["history"].append(entry)

def update_status(download_id: str, data: dict):
    with _lock:
        _ensure_initialized(download_id)
        now = int(time())
        status_entry = _status_map[download_id]

        # merge updates
        for k, v in data.items():
            status_entry[k] = v

        status_entry["timestamp"] = now
        _timestamp_map[download_id] = now

        # add to history
        _log_history(download_id, "update", data)

        # completed/error state tracking
        if data.get("status") in {"completed", "converted", "error", "canceled"}:
            status_entry["completed_at"] = now

def safe_complete(download_id: str, filepath: str = None):
    with _lock:
        _ensure_initialized(download_id)
        now = int(time())
        if filepath and os.path.exists(filepath):
            size = os.path.getsize(filepath)
            if size >= MIN_VALID_FILESIZE:
                _status_map[download_id].update({
                    "status": "completed",
                    "completed_at": now,
                    "timestamp": now,
                    "filename": os.path.basename(filepath),
                    "filesize": size
                })
                _log_history(download_id, "completed", {"file": filepath, "size": size})
                return True
            else:
                update_status(download_id, {
                    "status": "error",
                    "message": f"File too small ({size} bytes), download likely failed.",
                    "error": "incomplete_file"
                })
                return False
        else:
            update_status(download_id, {
                "status": "error",
                "message": "Download file missing or invalid.",
                "error": "missing_file"
            })
            return False

def get_status(download_id: str, deep_copy=True) -> dict:
    with _lock:
        _ensure_initialized(download_id)
        status = _status_map.get(download_id, DEFAULT_STATUS.copy())
        return copy.deepcopy(status) if deep_copy else status

def clear_status(download_id: str):
    with _lock:
        _status_map.pop(download_id, None)
        _timestamp_map.pop(download_id, None)

def cleanup_stale_statuses(timeout_seconds=3600, remove_completed=True):
    """Remove old statuses after `timeout_seconds` of inactivity."""
    with _lock:
        now = int(time())
        stale_ids = []
        for did, ts in _timestamp_map.items():
            st = _status_map.get(did, {})
            if now - ts > timeout_seconds:
                if remove_completed or st.get("status") not in {"completed", "converted"}:
                    stale_ids.append(did)
        for did in stale_ids:
            _status_map.pop(did, None)
            _timestamp_map.pop(did, None)

def list_all_statuses(include_meta=False, deep_copy=True) -> dict:
    with _lock:
        if include_meta:
            return copy.deepcopy(_status_map) if deep_copy else _status_map
        else:
            return {
                k: {
                    "status": v["status"],
                    "progress": v["progress"],
                    "speed": v["speed"],
                    "video_url": v["video_url"],
                    "file_type": v.get("file_type", "video"),
                    "filename": v.get("filename")
                }
                for k, v in _status_map.items()
            }

def mark_error(download_id: str, error_message: str):
    update_status(download_id, {
        "status": "error",
        "error": error_message,
        "message": "Download failed",
        "completed_at": int(time())
    })
    _log_history(download_id, "error", {"error": error_message})

def mark_cancelled(download_id: str):
    update_status(download_id, {
        "status": "canceled",
        "message": "Download canceled by user",
        "completed_at": int(time())
    })
    _log_history(download_id, "canceled")
