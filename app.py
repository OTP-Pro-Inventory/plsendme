from flask import Flask, request, jsonify, send_from_directory, session, redirect, url_for, render_template
from flask_cors import CORS
from functools import wraps
import json
import os

app = Flask(__name__)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

# Sample user database
USERS = {
    "sallen": "Bigmac100",
    "bgaines": "Cheese100"
}

app = Flask(__name__, static_folder="static", static_url_path="")
CORS(app)  # Enable CORS
app.secret_key = "your-secret-key"

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
    
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username in USERS and USERS[username] == password:
            session["username"] = username
            return redirect(url_for("serve_index"))
        else:
            return render_template("login.html", error="Invalid username or password")
    return render_template("login.html")

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

@app.route("/")
@login_required
def serve_index():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
