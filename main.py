import threading
import uvicorn

from config.server_config import FINAL_IP, SERVER_URL, create_app, SERVER_PORT
from api_registory import register_all_routes
from utils.cleaner import run_cleaner

app = create_app()
register_all_routes(app)

def start_cleaner_in_background():
    cleaner_thread = threading.Thread(
        target=run_cleaner,
        daemon=True
    )
    cleaner_thread.start()

if __name__ == "__main__":
    print(f"[!] INFO: Starting SavifyPro Server on {FINAL_IP}")
    print(f"[!] INFO: Access the API at {SERVER_URL}")
    start_cleaner_in_background()
    uvicorn.run("main:app",
        host="0.0.0.0",
        port=SERVER_PORT,
        reload=True
    )
