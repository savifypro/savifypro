import uvicorn
from config.server_config import FINAL_IP, SERVER_URL, create_app, SERVER_PORT
from api_registory import register_all_routes

app = create_app()
register_all_routes(app)

if __name__ == "__main__":
    print(f"[!] INFO: Starting SavifyPro Server on {FINAL_IP}")
    print(f"[!] INFO: Access the API at {SERVER_URL}")
    uvicorn.run("main:app", host="0.0.0.0", port=SERVER_PORT, reload=True)