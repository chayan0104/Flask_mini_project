import os
import sqlite3
import time
from contextlib import closing

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

DATABASE_PATH = os.getenv(
    "DATABASE_PATH", os.path.join(os.path.dirname(__file__), "users.sqlite3")
)
SERVICE_NAME = "users"
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


def connect_database():
    return sqlite3.connect(DATABASE_PATH, timeout=30)


def initialize_database():
    with closing(connect_database()) as connection, connection:
        connection.execute(
            "CREATE TABLE IF NOT EXISTS users ("
            "id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE)"
        )
        connection.executemany(
            "INSERT OR IGNORE INTO users (name) VALUES (?)",
            [("Alice",), ("Bob",), ("Charlie",)],
        )


def add_user(name):
    with closing(connect_database()) as connection, connection:
        connection.execute("INSERT INTO users (name) VALUES (?)", (name,))


initialize_database()


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


@app.route("/api/users")
def get_users():
    with closing(connect_database()) as connection, connection:
        rows = connection.execute("SELECT name FROM users ORDER BY id").fetchall()
    return jsonify(users=[row[0] for row in rows])


@app.route("/api/users", methods=["POST"])
def create_user():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict) or not isinstance(payload.get("name"), str):
        return jsonify(error="A non-empty name is required"), 400

    name = payload["name"].strip()
    if not name:
        return jsonify(error="A non-empty name is required"), 400

    try:
        add_user(name)
    except sqlite3.IntegrityError:
        return jsonify(error="User already exists"), 409

    return jsonify(name=name), 201


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