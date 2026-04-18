from fastapi.testclient import TestClient
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.main import app

client = TestClient(app)

# Test registration
print("Testing registration...")
import datetime
username = f'testuser_{int(datetime.datetime.now().timestamp() * 1000)}'
response = client.post("/api/auth/register", json={
    "username": username,
    "email": f"{username}@example.com",
    "password": "password123"
})
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")

if response.status_code == 200:
    data = response.json()
    token = data.get('access_token')
    print(f"\nToken: {token}")
    
    # Test authenticated request
    print("\n\nTesting authenticated request...")
    headers = {"Authorization": f"Bearer {token}"}
    print(f"Headers: {headers}")
    
    response = client.get("/api/auth/me", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
else:
    print("Registration failed")
