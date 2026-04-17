import asyncio
import json
import websockets
from app_state import AppState

class WSClient:
    def __init__(self, state: AppState, hub_ip: str = "192.168.4.1"):
        self.state = state
        self.hub_ip = hub_ip
        self.ws_connection = None

    async def connect(self):
        uri = f"ws://{self.hub_ip}:81"
        try:
            async with websockets.connect(uri) as websocket:
                self.ws_connection = websocket
                self.state.hub_connected = True
                self.state.update()
                
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        if data.get("type") == "sensor_data":
                            self.state.temp_val = str(data.get('temperature', self.state.temp_val))
                            self.state.hum_val = str(data.get('humidity', self.state.hum_val))
                            self.state.sensor_connected = True
                        elif data.get("type") == "relay_state":
                            self.state.relay_state = bool(data.get("state", False))
                            self.state.relay_connected = True
                        elif data.get("type") == "relay_connection":
                            self.state.relay_connected = bool(data.get("connected", False))
                        elif data.get("type") == "sensor_connection":
                            self.state.sensor_connected = bool(data.get("connected", False))
                        self.state.update()
                    except json.JSONDecodeError:
                        pass
        except Exception as e:
            print(f"WS error: {e}")
        finally:
            self.ws_connection = None
            self.state.hub_connected = False
            self.state.relay_connected = False
            self.state.sensor_connected = False
            self.state.update()
            
            # Попытка переподключения через 5 секунд
            await asyncio.sleep(5)
            asyncio.create_task(self.connect())

    async def toggle_relay(self, relay_on: bool):
        self.state.relay_state = relay_on
        if self.ws_connection and self.state.relay_connected:
            state_int = 1 if relay_on else 0
            try:
                await self.ws_connection.send(f"relay/set/{state_int}")
            except Exception as ex:
                print(f"Failed to send relay command: {ex}")
        self.state.update()
