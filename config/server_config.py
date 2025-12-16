import os
import socket
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

LOCAL_PROTOCOL = "http"
LOCAL_IP = socket.gethostbyname(socket.gethostname())
LOCAL_PORT = 8000

PRODUCTION_PROTOCOL = "https"
PRODUCTION_SUBDOMAIN = "api"
PRODUCTION_DOMAIN = "savifypro"
PRODUCTION_EXTENSION = "com"

FINAL_IP = f"{LOCAL_PROTOCOL}://{LOCAL_IP}:{LOCAL_PORT}"

ENVIRONMENT = os.getenv("SERVER_ENV", "production").lower().strip()

if ENVIRONMENT == "local":
    SERVER_HOST = LOCAL_IP
    SERVER_PORT = LOCAL_PORT
    SERVER_URL = f"{LOCAL_PROTOCOL}://{LOCAL_IP}:{LOCAL_PORT}"
else:
    SERVER_HOST = "0.0.0.0"
    SERVER_PORT = 8000
    SERVER_URL = f"{PRODUCTION_PROTOCOL}://{PRODUCTION_SUBDOMAIN}.{PRODUCTION_DOMAIN}.{PRODUCTION_EXTENSION}"


def create_app():
    app = FastAPI(
        title="SavifyPro Server",
        description="FastAPI backend for SavifyPro",
        version="1.0.0"
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app


if __name__ == "__main__":
    print(f"[CONFIG] Environment: {ENVIRONMENT}")
    print(f"[CONFIG] SERVER_URL: {SERVER_URL}")
    print(f"[CONFIG] FINAL_IP: {FINAL_IP}")
    print(f"[CONFIG] HOST: {SERVER_HOST}, PORT: {SERVER_PORT}")

    app = create_app()
    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT)
