from flask import Flask, request, jsonify, session, redirect, url_for, render_template
from flask_cors import CORS
from functools import wraps
import json
import os
from datetime import datetime

# Initialize Flask app
app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)

# Configuration
app.secret_key = os.environ.get('SECRET_KEY') or 'dev-secret-key-here'
app.config['DATA_FOLDER'] = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(app.config['DATA_FOLDER'], exist_ok=True)

# User authentication - consider using proper database in production
USERS = {
    "sallen": "Bigmac100",
    "bgaines": "Cheese100"
}

# File paths
INVENTORY_FILE = os.path.join(app.config['DATA_FOLDER'], 'inventory.json')
REMOVALS_FILE = os.path.join(app.config['DATA_FOLDER'], 'removals.json')
ACTIVITY_FILE = os.path.join(app.config['DATA_FOLDER'], 'activity.json')

def initialize_data_files():
    """Create data files if they don't exist"""
    for file_path in [INVENTORY_FILE, REMOVALS_FILE, ACTIVITY_FILE]:
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                json.dump([], f)

initialize_data_files()

def read_json(file_path):
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def write_json(file_path, data):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

def log_activity(username, action):
    """Record user activities with timestamp"""
    activity = {
        "user": username,
        "action": action,
        "timestamp": datetime.now().isoformat()
    }
    activities = read_json(ACTIVITY_FILE)
    activities.append(activity)
    write_json(ACTIVITY_FILE, activities)

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ======================
# ROUTES
# ======================

# Main pages
@app.route('/')
@login_required
def index():
    log_activity(session['username'], 'Accessed dashboard')
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username in USERS and USERS[username] == password:
            session['username'] = username
            log_activity(username, 'Logged in')
            return redirect(url_for('index'))
        
        return render_template('login.html', error='Invalid credentials')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    if 'username' in session:
        log_activity(session['username'], 'Logged out')
        session.pop('username', None)
    return redirect(url_for('login'))

# Inventory routes
@app.route('/inventory')
@login_required
def inventory():
    log_activity(session['username'], 'Viewed inventory')
    return render_template('inventory.html')

@app.route('/add-item')
@login_required
def add_item():
    log_activity(session['username'], 'Accessed add item')
    return render_template('add_item.html')

@app.route('/removals')
@login_required
def removals():
    log_activity(session['username'], 'Viewed removals')
    return render_template('removals.html')

@app.route('/activity-log')
@login_required
def activity_log():
    log_activity(session['username'], 'Viewed activity log')
    return render_template('activity_log.html')

# API Endpoints
@app.route('/api/inventory', methods=['GET', 'POST'])
@login_required
def api_inventory():
    if request.method == 'GET':
        return jsonify(read_json(INVENTORY_FILE))
    else:
        data = request.get_json()
        write_json(INVENTORY_FILE, data)
        log_activity(session['username'], 'Updated inventory')
        return jsonify({'status': 'success'})

@app.route('/api/removals', methods=['GET', 'POST'])
@login_required
def api_removals():
    if request.method == 'GET':
        return jsonify(read_json(REMOVALS_FILE))
    else:
        data = request.get_json()
        write_json(REMOVALS_FILE, data)
        log_activity(session['username'], 'Updated removals')
        return jsonify({'status': 'success'})

@app.route('/api/activity', methods=['GET'])
@login_required
def api_activity():
    return jsonify(read_json(ACTIVITY_FILE))

# ======================
# RUN APPLICATION
# ======================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
