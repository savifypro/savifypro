# core/components/video_info_getter.py

from core.engine.metadata_extractor import extract_metadata

def get_video_info(url, headers=None, download_id=None):
    return extract_metadata(url, headers=headers, download_id=download_id)