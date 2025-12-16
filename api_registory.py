# route_registory.py

from config.routes_config import register_api_routes

def register_all_routes(app):
    register_api_routes(app)