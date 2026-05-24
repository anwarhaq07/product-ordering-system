from app.main import app
import threading

#Authorzation helper function
def register_user(client, username, password, role="customer"):

    return client.post("/register", json={
        "username": username,
        "password":password,
        "role":role
    })

def login_user(client, username, password):

    response = client.post(
        "/login",
        data={
            "username": username,
            "password": password
        }
    )
    return response.json()["access_token"]

def auth_headers(token):

    return{
        "Authorization": f"Bearer {token}"
    }

def create_order_requires_auth(client):

    response = client.post("/orders", json={
        "customer_name": "Test",
        "product_id":1,
        "quantity_kg":1
    })

    assert response.status_code == 401

def test_invalid_token_rejected(client):

    response= client.post(
        "/orders",
        json={
            "customer_name": "Test",
            "product_id":1,
            "quantity_kg": 1
        },
        headers={
            "Authorization": "Bearer fake_token"
        }
    )

    assert response.status_code == 401

def test_create_order_success(client):
    register_user(client, "user1", "pass123")
    token = login_user(client, "user1", "pass123")
    response = client.post("/orders", json={
        "customer_name": "Test User",
        "product_id" : 1,
        "quantity_kg" : 2
    },
    headers = auth_headers(token)
    )
    print(response.status_code)
    print(response.json())
    assert response.status_code == 200

def test_stock_reduction_after_order(client):

    register_user(client, "user1", "pass123")

    token = login_user(client, "user1", "pass123")
    #create order
    response = client.post("/orders", json={
        "customer_name": "user1",
        "product_id": 1,
        "quantity_kg": 2
    },
    headers = auth_headers(token)
    )

    assert response.status_code == 200

    #Fetch products
    products = client.get("/products").json()

    #Find product 1
    product = next(p for p in products if p["id"] == 1)

    assert product["stock_kg"] >= 0

def test_cannot_oversell(client):

    register_user(client, "user1", "pass123")

    token = login_user(client, "user1", "pass123")    

    #Try ordering huge quantity
    response = client.post("/orders", json={
        "customer_name": "user1",
        "product_id" : 1,
        "quantity_kg": 10000
    }, 
    headers=auth_headers(token)
    
    )

    assert response.status_code == 400

def test_cancel_restores_stock(client):

    register_user(client, "user1", "pass123")

    token = login_user(client, "user1", "pass123")
    #Create order
    response = client.post("/orders", json={
        "customer_name": "Test User",
        "product_id":1,
        "quantity_kg": 2
    },
    headers=auth_headers(token)
    )

    order_id = response.json()["order_id"]

    #cancel order
    cancel = client.post(f"/orders/{order_id}/cancel", headers=auth_headers(token))
    assert cancel.status_code == 200

    #verify stock restored
    products = client.get("/products").json()
    product = next(p for p in products if p["id"] == 1)

    assert product["stock_kg"] >= 0

def test_cannot_cancel_delivered_order(client):

    register_user(client, "user1", "pass123")

    token = login_user(client, "user1", "pass123")
    # Create order
    response = client.post("/orders", json={
        "customer_name": "Test User",
        "product_id": 1,
        "quantity_kg": 1
    },
    headers=auth_headers(token)
    )

    order_id = response.json()["order_id"]

    # Confirm
    client.post(f"/prders/{order_id}/confirm")

    #Deliver
    client.post(f"/prders/{order_id}/deliver")

    #Try cancel
    cancel = client.post(f"/prders/{order_id}/cancel")

    assert cancel.status_code == 404

def test_cannot_cancel_twice(client):

    register_user(client, "user1", "pass123")

    token = login_user(client, "user1", "pass123")

    response = client.post("/orders", json={
        "customer_name": "Test User",
        "product_id": 1,
        "quantity_kg": 1
    },
    headers=auth_headers(token)
    )

    order_id = response.json()["order_id"]

    client.post(f"/orders/{order_id}/cancel", headers=auth_headers(token))

    second = client.post(f"/orders/{order_id}/cancel", headers=auth_headers(token))

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

def test_idempotent_concurrent(client):
    headers = {"Idempotency-key":"same-key"}

    results = []

    def place():
        r = client.post("/orders", json={
            "customer_name": "Test",
            "product_id": 1,
            "quantity_kg": 2
        }, headers = headers)
        results.append(r.json())

        t1 = threading.Thread(target=place)
        t2 = threading.Thread(target=place)

        t1.start(); t2.start()
        t1.join();t2.join()

        assert results[0] == results[1]

#Test that a user can cancel their own order
def test_owner_can_cancel_own_order(client):

    register_user(client, "user1", "pass123")
    token = login_user(client, "user1", "pass123")

    headers = auth_headers(token)

    response = client.post(
        "/orders",
        json = {
            "customer_name" : "User1",
            "product_id": 1,
            "quantity_kg": 1
        },
        headers=headers
    )
    assert response.status_code == 200
    order_id = response.json()["order_id"]
    cancel=client.post(
        f"/orders/{order_id}/cancel",
        headers=headers
    )
    assert cancel.status_code == 200

def test_unauthenticated_owner_blocked(client):
    register_user(client, "alice", "pass123")
    alice_token = login_user(client, "alice", "pass123")
    alice_headers = auth_headers(alice_token)

    register_user(client, "bob", "pass123")
    bob_token = login_user(client, "bob", "pass123")
    bob_headers = auth_headers(bob_token)

    response = client.post(
        "/orders",
        json = {
            "customer_name": "Alice",
            "product_id": 1,
            "quantity_kg": 1
        },
        headers=alice_headers
    )

    order_id = response.json()["order_id"]

    cancel = client.post(
        f"/orders/{order_id}/cancel",
        headers=bob_headers
    )
    assert cancel.status_code == 403

#Customer Blocked from confirming the order
def test_customer_cannot_confirm_order(client):
    register_user(client,"customer1","pass123")
    token = login_user(client, "customer1", "pass123")
    headers = auth_headers(token)

    create_response = client.post(
        "/orders",
        json={
            "customer_name": "Customer1",
            "product_id": 1,
            "quantity_kg": 1
        },
        headers=headers
    )
    order_id = create_response.json()["order_id"]

    response = client.post(
        f"/orders/{order_id}/confirm",
        headers=headers
    )
    assert response.status_code == 403

#ADMIN can confirm order
def test_admin_can_confirm(client):
    register_user(client, "admin1", "pass123", role="admin")
    token = login_user(client, "admin1", "pass123")
    headers = auth_headers(token)

    register_user(client, "customer1", "pass123")
    customer1_token = login_user(client, "customer1", "pass123")
    customer_headers = auth_headers(customer1_token)

    create_response = client.post(
        "/orders",
        json={
            "customer_name": "Customer1",
            "product_id": 1,
            "quantity_kg": 1
        },
        headers = customer_headers
    )
    order_id = create_response.json()["order_id"]

    response = client.post(
        f"/orders/{order_id}/confirm",
        headers=headers
    )

    assert response.status_code != 403