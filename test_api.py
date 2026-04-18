import httpx
import asyncio
import json

async def test_api():
    # Test registration
    async with httpx.AsyncClient() as client:
        print("Testing registration...")
        import datetime
        username = f'testuser_{datetime.datetime.now().timestamp()}'.replace('.', '')
        r = await client.post('http://localhost:8000/api/auth/register', 
            json={'username': username, 'email': f'{username}@example.com', 'password': 'password123'})
        print(f"Status: {r.status_code}")
        print(f"Response: {json.dumps(r.json(), indent=2)}")
        
        if r.status_code == 200:
            data = r.json()
            token = data.get('access_token')
            print(f"\n✅ Registration successful! Token: {token[:20]}...")
            
            # Test an authenticated request
            print("\nTesting authenticated request...")
            r2 = await client.get('http://localhost:8000/api/auth/me',
                headers={'Authorization': f'Bearer {token}'})
            print(f"Status: {r2.status_code}")
            print(f"Response: {json.dumps(r2.json(), indent=2)}")

asyncio.run(test_api())
