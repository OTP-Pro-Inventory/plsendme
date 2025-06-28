import os
import json
import uuid
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this to a secure secret key

# Ensure data directory exists
if not os.path.exists('data'):
    os.makedirs('data')

# Initialize inventory.json if it doesn't exist
if not os.path.exists('data/inventory.json'):
    with open('data/inventory.json', 'w') as f:
        json.dump([], f)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/inventory')
def inventory():
    try:
        with open('data/inventory.json', 'r') as f:
            inventory_data = json.load(f)
        return render_template('inventory.html', inventory=inventory_data)
    except Exception as e:
        flash(f"Error loading inventory: {str(e)}", "error")
        return render_template('inventory.html', inventory=[])

@app.route('/add-item', methods=['GET'])
def add_item_form():
    return render_template('add_item.html')

@app.route('/add-item', methods=['POST'])
def add_item():
    try:
        # Get form data
        new_item = {
            "id": str(uuid.uuid4()),
            "name": request.form.get('name'),
            "upc": request.form.get('upc'),
            "model": request.form.get('model'),
            "quantity": int(request.form.get('quantity')),
            "threshold": int(request.form.get('threshold')),
            "category": "Electronics",  # Default category
            "timestamp": datetime.now().isoformat()
        }

        # Load current inventory
        with open('data/inventory.json', 'r') as f:
            inventory = json.load(f)

        # Add new item
        inventory.append(new_item)

        # Save updated inventory
        with open('data/inventory.json', 'w') as f:
            json.dump(inventory, f, indent=2)

        flash('Item successfully added to inventory!', 'success')
        return redirect(url_for('inventory'))

    except Exception as e:
        flash(f'Error adding item: {str(e)}', 'error')
        return redirect(url_for('add_item_form'))

@app.route('/api/inventory', methods=['GET'])
def get_inventory():
    try:
        with open('data/inventory.json', 'r') as f:
            inventory = json.load(f)
        return jsonify(inventory)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/record-removal', methods=['POST'])
def record_removal():
    try:
        data = request.get_json()
        item_id = data.get('itemId')
        amount = int(data.get('amount'))
        
        # Load current inventory
        with open('data/inventory.json', 'r') as f:
            inventory = json.load(f)
        
        # Find and update item
        for item in inventory:
            if item['id'] == item_id:
                item['quantity'] -= amount
                break
        
        # Save updated inventory
        with open('data/inventory.json', 'w') as f:
            json.dump(inventory, f, indent=2)
        
        # Record removal in history (you'll need to implement this)
        # save_removal_history(data)
        
        return jsonify({"success": True, "message": "Removal recorded successfully"})
    
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/removals')
def removals():
    # Implement this to show removal history
    return render_template('removals.html')

@app.route('/activity-log')
def activity_log():
    # Implement this to show activity log
    return render_template('activity_log.html')

@app.route('/logout')
def logout():
    # Implement proper logout functionality
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
