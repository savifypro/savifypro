import os
from fastapi import FastAPI, Body, File, Query, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from config.server_config import FINAL_IP
from core import get_video_info, start_download, start_audio_download
from dir_setup import AUDIO_DIR, VIDEO_DIR
from utils.converter import convert_video_to_audio, delete_file, save_uploaded_file
from utils.status_manager import get_status

def register_api_routes(app: FastAPI):

    audio_dir = "data/audio"
    os.makedirs(audio_dir, exist_ok=True)
    app.mount("/api/download", StaticFiles(directory=audio_dir), name="download")

    @app.get("/")
    async def home():
        """Serve the root index.html file directly"""
        filepath = os.path.join("index.html")
        if not os.path.isfile(filepath):
            return JSONResponse({"error": "index.html not found"}, status_code=404)
        return FileResponse(filepath, media_type="text/html")

    @app.get("/download/video/{filename:path}")
    async def serve_video(filename: str):
        return await serve_media_file(VIDEO_DIR, filename)

    @app.get("/download/audio/{filename:path}")
    async def serve_audio_file(filename: str):
        return await serve_media_file(AUDIO_DIR, filename)

    async def serve_media_file(directory: str, filename: str):
        try:
            filepath = os.path.join(directory, filename)
            if not os.path.isfile(filepath):
                return JSONResponse({"error": "File not found"}, status_code=404)
            ext = os.path.splitext(filename)[1].lower()
            mime_type = {
                ".mp4": "video/mp4",
                ".webm": "video/webm",
                ".mkv": "video/x-matroska",
                ".mov": "video/quicktime",
                ".mp3": "audio/mpeg",
                ".m4a": "audio/mp4",
                ".aac": "audio/aac",
                ".ogg": "audio/ogg",
                ".wav": "audio/wav"
            }.get(ext, "application/octet-stream")
            return FileResponse(
                filepath,
                media_type=mime_type,
                filename=filename,
                headers={"Access-Control-Allow-Origin": "*"}
            )
        except Exception as e:
            return JSONResponse({"error": f"Failed to serve file: {str(e)}"}, status_code=500)

    @app.post("/api/fetch")
    async def api_extract(payload: dict = Body(...)):
        try:
            url = payload.get("url", "").strip()
            if not url:
                return JSONResponse({"error": "URL is required"}, status_code=400)
            return get_video_info(url)
        except Exception as e:
            return JSONResponse({"error": f"Failed to extract info: {str(e)}"}, status_code=500)

    @app.post("/api/video/download")
    async def api_video_download(payload: dict = Body(...)):
        try:
            url = payload.get("url", "").strip()
            quality = payload.get("quality", "").strip()
            type_ = payload.get("type", "video").strip().lower()
            if not url or not quality:
                return JSONResponse({"error": "Missing URL or quality"}, status_code=400)
            download_id = start_download(url, quality, type_)
            return {"download_id": download_id, "status": "started"}
        except Exception as e:
            return JSONResponse({"error": f"Failed to start download: {str(e)}"}, status_code=500)

    @app.post("/api/audio/download")
    async def api_audio_download(payload: dict = Body(...)):
        try:
            url = payload.get("url", "").strip()
            format_id = payload.get("format_id", "").strip()
            headers = payload.get("headers", {})
            if not url or not format_id:
                return JSONResponse({"error": "Missing URL or format ID"}, status_code=400)
            download_id = start_audio_download(url, format_id, headers)
            return {"download_id": download_id, "status": "started"}
        except Exception as e:
            return JSONResponse({"error": f"Failed to start audio download: {str(e)}"}, status_code=500)

    @app.get("/api/status/{download_id}")
    async def api_status(download_id: str):
        try:
            data = get_status(download_id)
            if not data:
                return JSONResponse({"error": "Invalid download ID"}, status_code=404)
            return data
        except Exception as e:
            return JSONResponse({"error": f"Status check failed: {str(e)}"}, status_code=500)

    @app.get("/api/check-updates")
    async def check_updates():
        try:
            return {
                "build_number": 6,
                "message": "New Update is Available! Please Download the Latest Version.",
                "apk_url": "https://savifypro.com/download-savifypro/"
            }
        except Exception as e:
            return JSONResponse({"error": f"Failed to fetch update info: {str(e)}"}, status_code=500)
        
    @app.get("/api/sonieffect/check-updates")
    async def check_sonieffect_updates():
        print("[!] INFO: Checking for updates")
        return {
            "build_number": 1,
            "new_version": "1.0.0",
            "message": "New Update is Available! Please Download the Latest Version.",
            "apk_url": "https://savifypro.com/download-sonieffect/"
        }    

    @app.post("/api/convert")
    async def convert(
        file: UploadFile = File(...),
        format: str = Query("mp3"),
        bitrate: str = Query("192k")
    ):
        try:
            print(f"[!] INFO: Uploading file: {file.filename}")
            
            # Save raw video file
            input_path = save_uploaded_file(file)
            print(f"[!] INFO: File saved: {input_path}")

            # Convert to audio
            print(f"[!] INFO: Converting {file.filename} to {format} at {bitrate} bitrate")
            output_path = convert_video_to_audio(
                input_path,
                out_format=format,
                bitrate=bitrate
            )

            filename = os.path.basename(output_path)
            print(f"[✓] DONE: Conversion completed, saved to {output_path}")

            return {
                "status": "success",
                "filename": filename,
                "download_url": f"{FINAL_IP}/api/download/{filename}"
            }

        except Exception as e:
            print(f"[✕] ERROR: Conversion failed - {str(e)}")
            return JSONResponse({"error": str(e)}, status_code=500)

    @app.delete("/api/delete/{filename}")
    async def delete_audio(filename: str):
        try:
            print(f"[!] INFO: Deleting file: {filename}")
            if delete_file(filename):
                print(f"[✓] DONE: File {filename} deleted successfully")
                return {"status": "deleted"}
            else:
                print(f"[!] WARNING: File {filename} not found")
                return JSONResponse({"error": "file not found"}, status_code=404)
        except Exception as e:
            print(f"[✕] ERROR: Deletion failed - {str(e)}")
            return JSONResponse({"error": str(e)}, status_code=500)
