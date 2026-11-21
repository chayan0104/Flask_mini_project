import os
import requests
from flask import Flask, jsonify
app = Flask(__name__)

# USERS_URL uses K8s DNS: http://users
USERS_URL = os.getenv("USERS_URL", "http://users")

@app.route("/api/orders")
def get_orders():
    try:
        # Service-to-Service Communication
        resp = requests.get(f"{USERS_URL}/api/users", timeout=2)
        resp.raise_for_status()
        return jsonify(order_id=101, status="pending", user_data=resp.json())
    except Exception as e:
        # Return 502 if downstream fails (crucial for troubleshooting)
        return jsonify(error=str(e), service="orders"), 502

@app.route("/health")
def health(): return "ok", 200