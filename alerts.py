# alerts.py
import asyncio
import websockets
import json
import logging
from config import RECONNECT_DELAY_SECONDS # Import reconnect delay

# Use module-specific logger
logger = logging.getLogger(__name__)

async def listen_for_alerts(websocket_url: str, subscription_msg: dict):
    """
    Connects to Whale Alert WebSocket, subscribes, yields parsed alert data,
    and handles reconnections.
    Based on test_alert.py logic.
    """
    if not websocket_url:
        logger.critical("WebSocket URL is not configured. Cannot connect.")
        return # Stop the generator if no URL

    subscribed_symbols = [s.lower() for s in subscription_msg.get("symbols", [])]
    if not subscribed_symbols:
        logger.error("No symbols defined in subscription message. Cannot filter alerts.")
        return

    logger.info(f"Will listen for alerts for symbols: {', '.join(subscribed_symbols).upper()}")

    while True: # Reconnection loop
        try:
            logger.info(f"Attempting WebSocket connection...")
            async with websockets.connect(websocket_url) as ws:
                logger.info("WebSocket connected. Subscribing...")
                await ws.send(json.dumps(subscription_msg))

                # Optional: Process initial response if needed
                try:
                     response = await asyncio.wait_for(ws.recv(), timeout=20) # Short timeout for subscription confirmation
                     logger.info(f"Subscription response: {response}")
                except asyncio.TimeoutError:
                     logger.warning("Did not receive subscription confirmation within 10s.")
                except Exception as conf_e:
                     logger.error(f"Error receiving subscription confirmation: {conf_e}")


                logger.info(f"Listening for alerts for {', '.join(subscribed_symbols).upper()}...")
                while True: # Message receiving loop
                    try:
                        # Wait longer for actual alerts, use config timeout? No, use indefinite wait.
                        # message_str = await asyncio.wait_for(ws.recv(), timeout=100) # Using wait_for is optional
                        message_str = await ws.recv() # Wait indefinitely

                        message_data = json.loads(message_str)

                        # Filter for relevant alerts (type and symbol)
                        message_symbol_lower = message_data.get('symbol', '').lower()
                        if message_data.get('type') == 'alert' and message_symbol_lower in subscribed_symbols:

                            # --- Start Parsing Logic (from test_alert.py) ---
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

                            # Safe access to amounts
                            amounts_list = message_data.get('amounts', [])
                            amount = 0
                            value_usd = 0
                            if amounts_list: # Check if list exists and is not empty
                                first_amount_dict = amounts_list[0]
                                if isinstance(first_amount_dict, dict):
                                    amount = first_amount_dict.get('amount', 0)
                                    value_usd = first_amount_dict.get('value_usd', 0)

                            parsed_alert = {
                                'symbol': message_data.get('symbol', 'UNKNOWN').upper(), # Store symbol
                                'blockchain': message_data.get('blockchain', 'unknown').upper(),
                                'amount': amount,
                                'value_usd': value_usd,
                                'from_owner': from_owner,
                                'to_owner': to_owner,
                                'timestamp': message_data.get('timestamp')
                            }
                            # --- End Parsing Logic ---

                            logger.info(f"Yielding parsed {parsed_alert['symbol']} alert.")
                            yield parsed_alert # Yield data to main.py

                        else:
                            # Log other message types if needed (DEBUG level recommended)
                            logger.debug(f"Ignoring non-target message: Type='{message_data.get('type')}', Symbol='{message_data.get('symbol')}'")

                    except json.JSONDecodeError:
                        logger.error(f"Failed to decode JSON: {message_str}")
                    except asyncio.TimeoutError: # If using wait_for
                        logger.debug('No message received within timeout window, continuing listen.')
                        # If NOT using wait_for, this won't be hit unless connection drops
                        continue
                    except websockets.ConnectionClosedOK:
                        logger.info("Inner loop detected connection closed normally.")
                        break # Break inner loop to trigger reconnect
                    except websockets.ConnectionClosedError as e:
                         logger.warning(f"Inner loop detected connection closed error: {e}")
                         break # Break inner loop to trigger reconnect
                    except Exception as e:
                        logger.error(f"Error processing message inside loop: {e}", exc_info=True)
                        # Decide whether to continue or break on processing errors

            # Handle connection errors that prevent the `async with` block
        except websockets.exceptions.InvalidStatusCode as e: # Catch specific handshake errors (like 429, 401)
            logger.error(f"WebSocket Handshake Failed: Status {e.status_code}. Check API Key/Rate Limits.")
            # No automatic retry on handshake failure? Or use longer delay?
            logger.info(f"Waiting {RECONNECT_DELAY_SECONDS * 4} seconds before retrying handshake...")
            await asyncio.sleep(RECONNECT_DELAY_SECONDS * 4) # Longer wait for auth/rate limit issues
            continue # Go to next iteration of outer loop
        except ConnectionRefusedError:
            logger.error(f"Connection refused by server. Retrying in {RECONNECT_DELAY_SECONDS * 2}s...")
            await asyncio.sleep(RECONNECT_DELAY_SECONDS * 2)
            continue
        except Exception as e: # Catch other connection errors (DNS, etc.)
            logger.error(f"WebSocket connection failed: {e}", exc_info=True)
                # Fall through to the standard reconnect delay

        # Wait before attempting reconnection in the outer loop
        logger.info(f"Waiting {RECONNECT_DELAY_SECONDS} seconds before attempting reconnect...")
        await asyncio.sleep(RECONNECT_DELAY_SECONDS)