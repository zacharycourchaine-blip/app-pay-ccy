import sqlite3
from datetime import datetime
from flask import Flask, request, jsonify, render_template
import requests
import os
from dotenv import load_dotenv

def init_db():
    conn = sqlite3.connect("payments.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT,
            amount TEXT,
            status TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()

# Load environment variables
load_dotenv()

app = Flask(__name__)

CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
SECRET = os.getenv("PAYPAL_SECRET")
print("CLIENT_ID:", CLIENT_ID)
print("SECRET:", SECRET)
BASE = "https://api-m.sandbox.paypal.com"


# 🔐 Get PayPal Access Token
def get_access_token():
    response = requests.post(
        f"{BASE}/v1/oauth2/token",
        auth=(CLIENT_ID, SECRET),
        data={"grant_type": "client_credentials"},
    )

    print("PAYPAL RESPONSE:", response.text)  # Debug

    data = response.json()
    return data.get("access_token")


# 🌐 Home page
@app.route("/")
def home():
    return render_template("index.html", client_id=CLIENT_ID)


# 💳 Create PayPal Order
@app.route("/create-order", methods=["POST"])
def create_order():
    amount = request.json.get("amount")

    token = get_access_token()

    if not token:
        return jsonify({"error": "Failed to get access token"}), 500

    response = requests.post(
        f"{BASE}/v2/checkout/orders",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        },
        json={
            "intent": "CAPTURE",
            "purchase_units": [{
                "amount": {
                    "currency_code": "USD",
                    "value": amount
                }
            }]
        },
    )

    return jsonify(response.json())


# ✅ Capture Payment
@app.route("/capture-order/<order_id>", methods=["POST"])
def capture_order(order_id):
    token = get_access_token()

    response = requests.post(
        f"{BASE}/v2/checkout/orders/{order_id}/capture",
        headers={"Authorization": f"Bearer {token}"},
    )

    data = response.json()
print("PAYPAL FULL RESPONSE:", data)

    try:
    purchase_units = data.get("purchase_units", [])
    if purchase_units:
        payments = purchase_units[0].get("payments", {})
        captures = payments.get("captures", [])
        if captures:
            amount = captures[0]["amount"]["value"]
        else:
            amount = "0"
    else:
        amount = "0"
except Exception as e:
    print("Amount extraction error:", e)
    amount = "0"

    # Save to database
    import sqlite3
    conn = sqlite3.connect("payments.db")
    c = conn.cursor()

    c.execute(
        "INSERT INTO payments (order_id, amount, status, created_at) VALUES (?, ?, ?, datetime('now'))",
        (order_id, amount, "COMPLETED")
    )

    conn.commit()
    conn.close()

    return jsonify(data)
    token = get_access_token()

    if not token:
        return jsonify({"error": "Failed to get access token"}), 500

    response = requests.post(
        f"{BASE}/v2/checkout/orders/{order_id}/capture",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    return jsonify(response.json())

@app.route("/dashboard")
def dashboard():
    import sqlite3
    conn = sqlite3.connect("payments.db")
    c = conn.cursor()

    c.execute("SELECT * FROM payments ORDER BY id DESC")
    payments = c.fetchall()

    conn.close()

    return render_template("dashboard.html", payments=payments)
# ▶️ Run app
init_db()
if __name__ == "__main__":
    app.run(debug=True)