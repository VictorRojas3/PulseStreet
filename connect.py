import asyncio
import websockets
import json

async def connect():
    api_key = "IfcyVkvWIWEv3nxIamXaoTAlhldbIikj"  # Please replace with your API key

    # The WebSocket API URL with the API key included
    url = f"wss://leviathan.whale-alert.io/ws?api_key={api_key}"
    print(url)
    # The subscription message
    subscription_msg = {
        "type": "subscribe_alerts",
        "blockchains": ["ethereum"],
        "symbols": ["eth"],
        "min_value_usd": 10_000,
    }

    # Connect to the WebSocket server
    async with websockets.connect(url) as ws:
        # Send the subscription message
        await ws.send(json.dumps(subscription_msg))

        # Wait for a response
        response = await ws.recv()

        # Print the response
        print(f"Received: {response}")

        # Continue to handle incoming messages
        while True:
            try:
                # Wait for a new message
                message = await asyncio.wait_for(ws.recv(), timeout=20)  # 20 seconds timeout
                print(f"Received: {message}")
            except asyncio.TimeoutError:
                print('Timeout error, closing connection')
                break
            except websockets.ConnectionClosed:
                print('Connection closed')
                break

# Run the connect function until it completes
asyncio.run(connect())