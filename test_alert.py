import asyncio
import websockets
import json
import logging
import os
import config
from config import WHALE_ALERT_API_KEY
print("WHALE_ALERT_API_KEY", WHALE_ALERT_API_KEY)
async def connect():
    api_key = WHALE_ALERT_API_KEY  
    print("API Key:", api_key)  

    url = f"wss://leviathan.whale-alert.io/ws?api_key={api_key}"

    subscription_msg = {
        "type": "subscribe_alerts",
        "blockchains": ["ethereum"],
        "symbols": ["eth"],
        "min_value_usd": 10_00,
    }

    async with websockets.connect(url) as ws:
        await ws.send(json.dumps(subscription_msg))

        response = await ws.recv()
        print(f"Response: {response}")
        while True:
            try:
                message_str = await asyncio.wait_for(ws.recv(), timeout=100)  
                message_data = json.loads(message_str)
                from_data = message_data.get('from') 
                to_data = message_data.get('to')

                if isinstance(from_data, dict):
                    from_owner = from_data.get('owner', from_data.get('owner_type', 'unknown'))
                elif isinstance(from_data, str):
                    from_owner = from_data
                else:
                    from_owner = 'unknown'

                if isinstance(to_data, dict):
                    to_owner = to_data.get('owner', to_data.get('owner_type', 'unknown'))
                elif isinstance(to_data, str):
                    to_owner = to_data
                else:
                    to_owner = 'unknown'

                parsed_alert = {
                    'blockchain': message_data.get('blockchain', 'unknown').upper(),
                    'amount': message_data.get('amounts', [{}])[0].get('amount', 0),
                    'value_usd': message_data.get('amounts', [{}])[0].get('value_usd', 0),
                    'from_owner': from_owner, 
                    'to_owner': to_owner,     
                    'timestamp': message_data.get('timestamp')
                }
                print(f"New alert 🚨🚨🚨 {parsed_alert}")
            except asyncio.TimeoutError:
                print('Timeout error, closing connection')
                break
            except websockets.ConnectionClosed:
                print('Connection closed')
                break

asyncio.run(connect())

