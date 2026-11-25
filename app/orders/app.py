import os
import time

import requests

from flask import Flask, Response, g, jsonify, request
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Histogram,
    REGISTRY,
    generate_latest,
    multiprocess,
)

app = Flask(__name__)

# USERS_URL uses K8s DNS: http://users
USERS_URL = os.getenv("USERS_URL", "http://users")
SERVICE_NAME = "orders"
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["service", "method", "endpoint", "status"],
)
REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["service", "method", "endpoint"],
)


@app.before_request
def start_request_timer():
    g.request_start_time = time.perf_counter()


@app.after_request
def record_request(response):
    if request.endpoint != "metrics":
        endpoint = request.url_rule.rule if request.url_rule else "unmatched"
        labels = (SERVICE_NAME, request.method, endpoint)
        REQUEST_COUNT.labels(*labels, str(response.status_code)).inc()
        REQUEST_DURATION.labels(*labels).observe(
            time.perf_counter() - g.request_start_time
        )
    return response


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


@app.route("/metrics")
def metrics():
    if os.getenv("PROMETHEUS_MULTIPROC_DIR"):
        registry = CollectorRegistry()
        multiprocess.MultiProcessCollector(registry)
    else:
        registry = REGISTRY
    return Response(
        generate_latest(registry),
        headers={"Content-Type": CONTENT_TYPE_LATEST},
    )


@app.route("/health")
def health(): return "ok", 200