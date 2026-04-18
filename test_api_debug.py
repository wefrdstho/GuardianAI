import httpx
import asyncio
import json
import base64

async def test_api():
    # Test registration
    async with httpx.AsyncClient() as client:
        print("Testing registration...")
        import datetime
        username = f'testuser_{datetime.datetime.now().timestamp()}'.replace('.', '')
        r = await client.post('http://localhost:8000/api/auth/register', 
            json={'username': username, 'email': f'{username}@example.com', 'password': 'password123'})
        print(f"Status: {r.status_code}")
        
        if r.status_code == 200:
            data = r.json()
            token = data.get('access_token')
            print(f"Token: {token}")
            
            # Decode token manually to inspect it
            print("\nDecoding token payload...")
            try:
                parts = token.split('.')
                payload = parts[1]
                # Add padding if needed
                payload += '=' * (4 - len(payload) % 4)
                decoded = base64.urlsafe_b64decode(payload)
                print(f"Decoded token payload: {json.loads(decoded)}")
            except Exception as e:
                print(f"Error decoding: {e}")
            
            # Test authentication
            print("\nTesting authenticated request...")
            headers = {'Authorization': f'Bearer {token}'}
            print(f"Headers: {headers}")
            r2 = await client.get('http://localhost:8000/api/auth/me', headers=headers)
            print(f"Status: {r2.status_code}")
            print(f"Response: {r2.json()}")

asyncio.run(test_api())
