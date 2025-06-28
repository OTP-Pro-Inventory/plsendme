from flask import Flask, request, jsonify, session, redirect, url_for, render_template, flash
from flask_cors import CORS
from functools import wraps
import json
import os
import uuid
from datetime import datetime

# Initialize Flask app
app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)

# Configuration
app.secret_key = os.environ.get('SECRET_KEY') or 'dev-secret-key-here'
app.config['DATA_FOLDER'] = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(app.config['DATA_FOLDER'], exist_ok=True)

# User authentication
USERS = {
    "sallen": "Bigmac100",
    "bgaines": "Cheese100"
}

# File paths
INVENTORY_FILE = os.path.join(app.config['DATA_FOLDER'], 'inventory.json')
REMOVALS_FILE = os.path.join(app.config['DATA_FOLDER'], 'removals.json')
ACTIVITY_FILE = os.path.join(app.config['DATA_FOLDER'], 'activity.json')

def initialize_data_files():
    """Create data files if they don't exist with initial data"""
    defaults = {
        INVENTORY_FILE: [
            {"id": "1", "name": "iPhone 13", "quantity": 8, "category": "Phones", "threshold": 5},
            {"id": "2", "name": "MacBook Pro", "quantity": 3, "category": "Laptops", "threshold": 5},
            {"id": "3", "name": "iPad Air", "quantity": 12, "category": "Tablets", "threshold": 5}
        ],
        REMOVALS_FILE: [],
        ACTIVITY_FILE: []
    }
    
    for file_path, default_data in defaults.items():
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                json.dump(default_data, f, indent=2)

initialize_data_files()

def read_json(file_path):
    """Read JSON data from file"""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def write_json(file_path, data):
    """Write data to JSON file"""
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

def log_activity(action):
    """Record user activities with timestamp"""
    if 'username' not in session:
        return
        
    activity = {
        "user": session['username'],
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
            flash('Please log in to access this page', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ======================
# AUTHENTICATION ROUTES
# ======================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username in USERS and USERS[username] == password:
            session['username'] = username
            log_activity(f"User {username} logged in")
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        
        flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    if 'username' in session:
        log_activity(f"User {session['username']} logged out")
        session.pop('username', None)
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

# ======================
# MAIN APPLICATION ROUTES
# ======================

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/inventory')
@login_required
def inventory():
    return render_template('inventory.html')

@app.route('/add-item', methods=['GET', 'POST'])
@login_required
def add_item():
    if request.method == 'POST':
        try:
            new_item = {
                "id": str(uuid.uuid4()),
                "name": request.form.get('name'),
                "upc": request.form.get('upc'),
                "model": request.form.get('model'),
                "quantity": int(request.form.get('quantity')),
                "threshold": int(request.form.get('threshold')),
                "category": request.form.get('category', 'Electronics'),
                "timestamp": datetime.now().isoformat()
            }
            
            inventory = read_json(INVENTORY_FILE)
            inventory.append(new_item)
            write_json(INVENTORY_FILE, inventory)
            
            log_activity(f"Added item: {new_item['name']}")
            flash('Item added successfully!', 'success')
            return redirect(url_for('inventory'))
            
        except Exception as e:
            flash(f'Error adding item: {str(e)}', 'danger')
    
    return render_template('add_item.html')

@app.route('/removals')
@login_required
def removals():
    return render_template('removals.html')

@app.route('/activity-log')
@login_required
def activity_log():
    return render_template('activity_log.html')

# ======================
# API ENDPOINTS (IMPROVED)
# ======================

@app.route('/api/stats')
@login_required
def get_stats():
    try:
        inventory = read_json(INVENTORY_FILE)
        stats = {
            "total_items": sum(item['quantity'] for item in inventory),
            "low_stock": sum(1 for item in inventory if item['quantity'] < item.get('threshold', 5)),
            "total_products": len(inventory)
        }
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/inventory', methods=['GET'])
@login_required
def get_inventory():
    try:
        return jsonify(read_json(INVENTORY_FILE))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/record-removal', methods=['POST'])
@login_required
def record_removal():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "No data provided"}), 400

        # Validate required fields
        required_fields = ['itemId', 'amount', 'employee', 'purpose']
        if not all(field in data for field in required_fields):
            return jsonify({"success": False, "message": "Missing required fields"}), 400

        item_id = data['itemId']
        amount = int(data['amount'])
        employee = data['employee']
        purpose = data['purpose']
        store = data.get('store', 'Not specified')

        if amount <= 0:
            return jsonify({"success": False, "message": "Amount must be positive"}), 400

        # Update inventory
        inventory = read_json(INVENTORY_FILE)
        item = next((item for item in inventory if item['id'] == item_id), None)
        
        if not item:
            return jsonify({"success": False, "message": "Item not found"}), 404
            
        if item['quantity'] < amount:
            return jsonify({"success": False, "message": "Insufficient quantity"}), 400
            
        item['quantity'] -= amount
        write_json(INVENTORY_FILE, inventory)
        
        # Record removal
        removal = {
            "id": str(uuid.uuid4()),
            "item_id": item_id,
            "item_name": item['name'],
            "amount": amount,
            "remaining": item['quantity'],
            "employee": employee,
            "purpose": purpose,
            "store": store,
            "timestamp": datetime.now().isoformat(),
            "processed_by": session['username']
        }
        
        removals = read_json(REMOVALS_FILE)
        removals.append(removal)
        write_json(REMOVALS_FILE, removals)
        
        log_activity(f"Recorded removal: {amount}x {item['name']} by {employee}")
        return jsonify({
            "success": True,
            "message": "Removal recorded successfully",
            "remaining": item['quantity']
        })
        
    except ValueError:
        return jsonify({"success": False, "message": "Invalid amount value"}), 400
    except Exception as e:
        app.logger.error(f"Error recording removal: {str(e)}")
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500

@app.route('/api/removals', methods=['GET'])
@login_required
def get_removals():
    try:
        return jsonify(read_json(REMOVALS_FILE))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/activity', methods=['GET'])
@login_required
def get_activity():
    try:
        return jsonify(read_json(ACTIVITY_FILE))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ======================
# RUN APPLICATION
# ======================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
