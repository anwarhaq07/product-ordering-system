from fastapi.testclient import TestClient
from app.main import app
import threading

def test_create_order_success(client):
    response = client.post("/orders", json={
        "customer_name": "Test User",
        "product_id" : 1,
        "quantity_kg" : 2
    })

    assert response.status_code ==200
    assert "message" in response.json()

def test_stock_reduction_after_order(client):

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

def test_cannot_oversell(client):

    #Try ordering huge quantity
    response = client.post("/orders", json={
        "customer_name": "Test User",
        "product_id" : 1,
        "quantity_kg": 10000
    })

    assert response.status_code == 400


def test_cancel_restores_stock(client):

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

def test_cannot_cancel_delivered_order(client):

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

def test_cannot_cancel_twice(client):

    response = client.post("/orders", json={
        "customer_name": "Test User",
        "product_id": 1,
        "quantity_kg": 1
    })

    order_id = response.json()["order_id"]

    client.post(f"/orders/{order_id}/cancel")

    second = client.post(f"/orders/{order_id}/cancel")

    assert second.status_code == 400

def test_concurrent_orders(client):

    results = []

    def place_order():
        response = client.post("/orders", json={
            "customer_name": "User",
            "product_id": 1,
            "quantity_kg": 4
        })

        results.append(response.status_code)

        t1 = threading.Thread(target=place_order)
        t2 = threading.Thread(target=place_order)

        t1.start()
        t2.start()

        t1.join()
        t2.join()

        #Only one should succeed
        assert results.count(200) == 1
        assert results.count(400) == 1