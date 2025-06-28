from flask import Flask, request, jsonify, send_from_directory, session, redirect, url_for, render_template
from flask_cors import CORS
from functools import wraps
import json
import os

app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)
app.secret_key = "your-secret-key"  # Change this to a secure key in production

# Sample user database
USERS = {
    "sallen": "Bigmac100",
    "bgaines": "Cheese100"
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INVENTORY_FILE = os.path.join(BASE_DIR, "inventory.json")
REMOVAL_FILE = os.path.join(BASE_DIR, "removal_history.json")
ACTIVITY_FILE = os.path.join(BASE_DIR, "activity_log.json")

def read_json(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

# HTML Page Routes
@app.route("/")
@login_required
def serve_index():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username in USERS and USERS[username] == password:
            session["username"] = username
            return redirect(url_for("serve_index"))
        return render_template("login.html", error="Invalid username or password")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))

@app.route("/inventory")
@login_required
def inventory_page():
    return render_template("inventory.html")

@app.route("/activity")
@login_required
def activity_page():
    return render_template("activity.html")

@app.route("/removals")
@login_required
def removals_page():
    return render_template("removals.html")

# API Endpoints (keep your existing ones)
@app.route("/api/inventory", methods=["GET", "PUT"])
@login_required
def inventory_api():
    if request.method == "GET":
        data = read_json(INVENTORY_FILE)
        return jsonify(data)
    else:
        new_data = request.get_json(force=True)
        write_json(INVENTORY_FILE, new_data)
        return jsonify({"status": "ok", "length": len(new_data)})

@app.route("/api/removals", methods=["GET", "PUT"])
@login_required
def removals_api():
    if request.method == "GET":
        data = read_json(REMOVAL_FILE)
        return jsonify(data)
    else:
        new_data = request.get_json(force=True)
        write_json(REMOVAL_FILE, new_data)
        return jsonify({"status": "ok", "length": len(new_data)})

@app.route("/api/activity", methods=["GET", "PUT"])
@login_required
def activity_api():
    if request.method == "GET":
        data = read_json(ACTIVITY_FILE)
        return jsonify(data)
    else:
        new_data = request.get_json(force=True)
        write_json(ACTIVITY_FILE, new_data)
        return jsonify({"status": "ok", "length": len(new_data)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
