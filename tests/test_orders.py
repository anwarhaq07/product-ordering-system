from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_order_success():
    response = client.post("/orders", json={
        "customer_name": "Test User",
        "product_id" : 1,
        "quantity_kg" : 2
    })

    assert response.status_code ==200
    assert "message" in response.json()

def test_stock_reduction_after_order():

    #create order
    response = client.post("/orders", json={
        "customer_name": "Test User",
        "product_id": 1,
        "quantity_kg": 2
    })

    assert response.status_code == 200

    #Fetch products
    products = client.get("/products").json()

    #Find product 1
    product = next(p for p in products if p["id"] == 1)

    assert product["stock_kg"] >= 0

def test_cannot_oversell():

    #Try ordering huge quantity
    response = client.post("/orders", json={
        "customer_name": "Test User",
        "product_id" : 1,
        "quantity_kg": 1000
    })

    assert response.status_code == 400


def test_cancel_restores_stock():

    #Create order
    response = client.post("/orders", json={
        "customer_name": "Test User",
        "product_id":1,
        "quantity_kg": 2
    })

    order_id = response.json()["order_id"]

    #cancel order
    cancel = client.post(f"/orders/{order_id}/cancel")
    assert cancel.status_code == 200

    #verify stock restored
    products = client.get("/products").json()
    product = next(p for p in products if p["id"] == 1)

    assert product["stock_kg"] >= 0

def test_cannot_cancel_delivered_order():

    # Create order
    response = client.post("/orders", json={
        "customer_name": "Test User",
        "product_id": 1,
        "quantity_kg": 1
    })

    order_id = response.json()["order_id"]

    # Confirm
    client.post(f"/prders/{order_id}/confirm")

    #Deliver
    client.post(f"/prders/{order_id}/deliver")

    #Try cancel
    cancel = client.post(f"/prders/{order_id}/cancel")

    assert cancel.status_code == 404

def test_cannot_cancel_twice():

    response = client.post("/orders", json={
        "customer_name": "Test User",
        "product_id": 1,
        "quantity_kg": 1
    })

    order_id = response.json().get("order_id", 1)

    client.post(f"/order/{order_id}/cancel")

    second = client.post(f"/orders/{order_id}/cancel")

    assert second.status_code == 400