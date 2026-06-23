"""
BillFlow Pro — Firebase Firestore Sync Engine
Asynchronously syncs SQLite data to Firebase Firestore using standard REST APIs.
"""
import threading
import requests
import json
import logging

# Configure logger
logger = logging.getLogger("firebase_sync")
logger.setLevel(logging.INFO)

def to_firestore_value(val):
    """Convert a Python value to a Firestore Value proto structure."""
    if val is None:
        return {"nullValue": None}
    elif isinstance(val, bool):
        return {"booleanValue": val}
    elif isinstance(val, (int, float)):
        return {"doubleValue": float(val)}
    elif isinstance(val, dict):
        return {"mapValue": {"fields": {k: to_firestore_value(v) for k, v in val.items()}}}
    elif isinstance(val, list):
        return {"arrayValue": {"values": [to_firestore_value(v) for v in val]}}
    else:
        # Check if it looks like an ISO timestamp or date
        return {"stringValue": str(val)}

def to_firestore_document(data):
    """Convert a flat or nested Python dict to Firestore Document fields."""
    return {"fields": {k: to_firestore_value(v) for k, v in data.items()}}

def sync_to_firebase_async(user_id, firebase_project_id, collection, doc_id, data, delete=False):
    """
    Launch a background thread to sync a record to Firebase Firestore.
    Runs asynchronously to ensure Flask responses remain extremely fast.
    """
    if not firebase_project_id or not user_id:
        return

    def run():
        try:
            url = f"https://firestore.googleapis.com/v1/projects/{firebase_project_id}/databases/(default)/documents/users/{user_id}/{collection}/{doc_id}"
            
            if delete:
                logger.info(f"Deleting document {doc_id} from {collection} in Firebase")
                response = requests.delete(url, timeout=10)
            else:
                logger.info(f"Syncing document {doc_id} to {collection} in Firebase")
                firestore_doc = to_firestore_document(data)
                # Use PATCH (update/create) to insert/overwrite document
                response = requests.patch(url, json=firestore_doc, timeout=10)
                
            if response.status_code not in (200, 201):
                logger.error(f"[-] Firebase Firestore sync failed: {response.text}")
            else:
                logger.info(f"[+] Firebase Firestore sync success for {collection}/{doc_id}")
        except Exception as err:
            logger.error(f"[-] Firebase sync exception: {err}")

    # Start daemon thread
    thread = threading.Thread(target=run, daemon=True)
    thread.start()

def sync_all_user_data(user_id, firebase_project_id, conn):
    """
    Perform a batch sync of all user tables (clients, products, invoices, payments, expenses) to Firebase.
    Returns the count of synced items per category.
    """
    results = {}
    if not firebase_project_id:
        return results

    # 1. Sync Clients
    clients = conn.execute("SELECT * FROM clients WHERE user_id = ? AND is_active = 1", (user_id,)).fetchall()
    results["clients"] = len(clients)
    for c in clients:
        sync_to_firebase_async(user_id, firebase_project_id, "clients", str(c["id"]), dict(c))

    # 2. Sync Products
    products = conn.execute("SELECT * FROM products WHERE user_id = ? AND is_active = 1", (user_id,)).fetchall()
    results["products"] = len(products)
    for p in products:
        sync_to_firebase_async(user_id, firebase_project_id, "products", str(p["id"]), dict(p))

    # 3. Sync Expenses
    expenses = conn.execute("SELECT * FROM expenses WHERE user_id = ?", (user_id,)).fetchall()
    results["expenses"] = len(expenses)
    for e in expenses:
        sync_to_firebase_async(user_id, firebase_project_id, "expenses", str(e["id"]), dict(e))

    # 4. Sync Invoices (including nested invoice items)
    invoices = conn.execute("SELECT * FROM invoices WHERE user_id = ?", (user_id,)).fetchall()
    results["invoices"] = len(invoices)
    for inv in invoices:
        inv_data = dict(inv)
        items = conn.execute("SELECT * FROM invoice_items WHERE invoice_id = ?", (inv["id"],)).fetchall()
        inv_data["items"] = [dict(item) for item in items]
        sync_to_firebase_async(user_id, firebase_project_id, "invoices", str(inv["id"]), inv_data)

    # 5. Sync Payments
    payments = conn.execute("SELECT * FROM payments WHERE user_id = ?", (user_id,)).fetchall()
    results["payments"] = len(payments)
    for pm in payments:
        sync_to_firebase_async(user_id, firebase_project_id, "payments", str(pm["id"]), dict(pm))

    return results


def check_and_sync_resource(user_id, collection, doc_id, data, conn, delete=False):
    """
    Check if the user has firebase sync enabled, and if so, sync the resource.
    """
    try:
        user = conn.execute("SELECT firebase_project_id, firebase_sync_enabled FROM users WHERE id = ?", (user_id,)).fetchone()
        if user and user["firebase_sync_enabled"] and user["firebase_project_id"]:
            sync_to_firebase_async(user_id, user["firebase_project_id"], collection, doc_id, data, delete)
    except Exception as e:
        logger.error(f"[-] Error checking firebase sync configuration: {e}")

