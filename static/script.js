
// Data structures
let inventory = [];
let removalHistory = [];
let activityLog = [];
let currentRemovalItem = null;

// Fetch data from server on load
window.onload = async function () {
    const path = window.location.pathname;
    const page = path.substring(path.lastIndexOf("/") + 1);

    try {
        const [invRes, remRes, actRes] = await Promise.all([
            fetch("/api/inventory"),
            fetch("/api/removals"),
            fetch("/api/activity")
        ]);

        inventory = await invRes.json();
        removalHistory = await remRes.json();
        activityLog = await actRes.json();
    } catch (err) {
        console.error("Could not load data:", err);
    }

    if (page === "inventory.html") {
        updateInventoryDisplay();
    } else if (page === "removals.html") {
        updateRemovalDisplay();
    } else if (page === "activity_log.html") {
        updateActivityLogDisplay();
    }
};

// Save data to server
async function saveData() {
    try {
        await fetch('/api/inventory', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(inventory)
        });
        await fetch('/api/removals', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(removalHistory)
        });
        await fetch('/api/activity', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(activityLog)
        });
    } catch (err) {
        console.error("Error saving data:", err);
    }
}

// Log activity and update display if on activity page
function logActivity(type, field, value, details = '') {
    const timestamp = new Date().toLocaleString();
    const entry = { timestamp, type, field, value, details };
    activityLog.unshift(entry);
    saveData();
    // If on activity page, update display
    const path = window.location.pathname;
    const page = path.substring(path.lastIndexOf("/") + 1);
    if (page === "activity_log.html") {
        updateActivityLogDisplay();
    }
}

// Add item to inventory
function addItem() {
    const name = document.getElementById('itemName').value.trim();
    const upc = document.getElementById('itemUPC').value.trim();
    const model = document.getElementById('itemModel').value.trim();
    const quantity = parseInt(document.getElementById('itemQuantity').value);
    if (!name || !upc || !model || quantity < 0) {
        alert('Please fill in all fields.');
        return;
    }
    const existing = inventory.find(i => i.upc === upc);
    if (existing) {
        existing.quantity += quantity;
        logActivity('Item Update', 'Added to Existing', `${name} (+${quantity})`, `Total: ${existing.quantity}`);
    } else {
        inventory.push({ name, upc, model, quantity });
        logActivity('Item Creation', 'New Item Added', name, `UPC: ${upc}, Model: ${model}, Qty: ${quantity}`);
    }
    saveData();
    updateInventoryDisplay();
    alert(`Added ${quantity} units of ${name}.`);
    document.getElementById('itemName').value = '';
    document.getElementById('itemUPC').value = '';
    document.getElementById('itemModel').value = '';
    document.getElementById('itemQuantity').value = 1;
}

// Update inventory display
function updateInventoryDisplay() {
    const inventoryList = document.getElementById('inventory-list');
    if (!inventoryList) return;

    if (inventory.length === 0) {
        inventoryList.innerHTML = '<div class="empty-state">No items in inventory.</div>';
        return;
    }

    inventoryList.innerHTML = inventory.map(item => `
        <div class="item-card">
            <div class="item-header">
                <div class="item-name">${item.name}</div>
                <div class="item-quantity">${item.quantity} units</div>
            </div>
            <div class="item-details">
                <div><strong>UPC:</strong> ${item.upc}</div>
                <div><strong>Model:</strong> ${item.model}</div>
            </div>
            <div class="item-controls">
                <button class="qty-btn" onclick="adjustQuantity('${item.upc}', 1)">+</button>
                <input type="number" class="qty-input" value="1" id="qty-${item.upc}" min="1">
                <button class="qty-btn" onclick="removeItems('${item.upc}')">-</button>
            </div>
        </div>
    `).join('');
}

// Adjust quantity (increment/decrement)
function adjustQuantity(upc, delta) {
    const item = inventory.find(i => i.upc === upc);
    if (!item) return;
    item.quantity += delta;
    if (item.quantity < 0) item.quantity = 0;
    logActivity('Quantity Adjust', 'Adjusted Quantity', item.name, `Now: ${item.quantity}`);
    saveData();
    updateInventoryDisplay();
}

// Open removal modal
function removeItems(upc) {
    const item = inventory.find(i => i.upc === upc);
    if (!item) return;
    const qtyInput = document.getElementById(`qty-${upc}`);
    const requested = parseInt(qtyInput.value) || 1;
    if (requested > item.quantity) {
        alert(`Cannot remove ${requested}. Only ${item.quantity} available.`);
        return;
    }
    currentRemovalItem = { item, amount: requested };
    document.getElementById('removalAmount').value = requested;
    document.getElementById('removalModal').style.display = 'block';
}

// Confirm removal
function confirmRemoval() {
    const employee = document.getElementById('employeeName').value.trim();
    const amount = parseInt(document.getElementById('removalAmount').value);
    const purpose = document.getElementById('removalPurpose').value.trim();
    const store = document.getElementById('storeSelect').value;
    if (!employee || !amount || !purpose || !store) {
        alert('Fill all fields.');
        return;
    }
    if (amount > currentRemovalItem.item.quantity) {
        alert(`Cannot remove ${amount}. Only ${currentRemovalItem.item.quantity} available.`);
        return;
    }
    currentRemovalItem.item.quantity -= amount;
    removalHistory.unshift({
        itemName: currentRemovalItem.item.name,
        model: currentRemovalItem.item.model,
        upc: currentRemovalItem.item.upc,
        amount,
        employee,
        purpose,
        store,
        date: new Date().toLocaleString()
    });
    logActivity('Item Removal', currentRemovalItem.item.name, `-${amount}`, `By ${employee} at ${store}`);
    if (currentRemovalItem.item.quantity === 0) {
        inventory = inventory.filter(i => i.upc !== currentRemovalItem.item.upc);
    }
    saveData();
    updateInventoryDisplay();
    // If on removals page, update display
    const path = window.location.pathname;
    const page = path.substring(path.lastIndexOf("/") + 1);
    if (page === "removals.html") {
        updateRemovalDisplay();
    }
    closeModal();
    alert(`Removed ${amount} units of ${currentRemovalItem.item.name}.`);
}

// Close modal
function closeModal() {
    document.getElementById('removalModal').style.display = 'none';
}

// Update removal history display
function updateRemovalDisplay() {
    const removalList = document.getElementById('removal-list');
    if (!removalList) return;
    if (removalHistory.length === 0) {
        removalList.innerHTML = '<div class="empty-state">No removal history.</div>';
        return;
    }
    removalList.innerHTML = removalHistory.map(r => `
        <div class="removal-item">
            <div class="removal-header">
                <span>${r.itemName} (${r.amount} units)</span>
                <span>${r.date}</span>
            </div>
            <div class="removal-details">
                <div><strong>Employee:</strong> ${r.employee}</div>
                <div><strong>Store:</strong> ${r.store}</div>
                <div><strong>UPC:</strong> ${r.upc} | <strong>Model:</strong> ${r.model}</div>
                <div><strong>Purpose:</strong> ${r.purpose}</div>
            </div>
        </div>
    `).join('');
}

// Update activity log display
function updateActivityLogDisplay() {
    const logContainer = document.getElementById('activity-log-container');
    if (!logContainer) return;
    if (activityLog.length === 0) {
        logContainer.innerHTML = '<div class="empty-state">No activity logged.</div>';
        return;
    }
    logContainer.innerHTML = activityLog.map(e => `
        <div class="log-entry">
            <div class="log-timestamp">${e.timestamp}</div>
            <div class="log-details"><strong>${e.type}:</strong> ${e.field} (${e.value}) ${e.details ? `<br><em>${e.details}</em>` : ''}</div>
        </div>
    `).join('');
}

// Close modal on outside click
window.onclick = function(event) {
    const modal = document.getElementById('removalModal');
    if (modal && event.target === modal) {
        closeModal();
    }
};
