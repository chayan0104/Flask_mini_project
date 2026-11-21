from flask import Flask, jsonify
app = Flask(__name__)

@app.route("/api/users")
def get_users():
    return jsonify(users=["Alice", "Bob", "Charlie"])

@app.route("/health")
def health(): return "ok", 200