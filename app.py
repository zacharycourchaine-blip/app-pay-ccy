from flask import Flask, request, jsonify, render_template
import requests
import os

app = Flask(__name__)

CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
SECRET = os.getenv("PAYPAL_SECRET")
BASE = "https://api-m.paypal.com"


def get_access_token():
    response = requests.post(
        f"{BASE}/v1/oauth2/token",
        auth=(CLIENT_ID, SECRET),
        data={"grant_type": "client_credentials"},
    )
    data = response.json()
    return data.get("access_token")


@app.route("/")
def home():
    return render_template("index.html", client_id=CLIENT_ID)


@app.route("/create-order", methods=["POST"])
def create_order():
    data = request.json
    amount = data.get("amount")

    token = get_access_token()

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


@app.route("/capture-order/<order_id>", methods=["POST"])
def capture_order(order_id):
    token = get_access_token()

    response = requests.post(
        f"{BASE}/v2/checkout/orders/{order_id}/capture",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    return jsonify(response.json())


if __name__ == "__main__":
    app.run(debug=True)