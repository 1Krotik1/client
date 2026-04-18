import asyncio
import json
import time
import websockets
from app_state import AppState

class WSClient:
    def __init__(self, state: AppState, hub_ip: str = "192.168.4.1"):
        self.state = state
        self.hub_ip = hub_ip
        self.ws_connection = None
        self.is_running = True

    async def connect(self):
        uri = f"ws://{self.hub_ip}:81"
        while self.is_running:
            try:
                async with websockets.connect(uri) as websocket:
                    self.ws_connection = websocket
                    self.state.hub_connected = True
                    self.state.update()

                    # Синхронизация времени хаба с клиентом
                    await websocket.send(f"time/sync/{int(time.time())}")
                    # Запросить текущую историю
                    await websocket.send("history/get")

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
                            elif data.get("type") == "history":
                                self.state.relay_history = data.get("relay", [])
                                self.state.sensor_history = data.get("sensor", [])
                            self.state.update()
                        except json.JSONDecodeError:
                            pass
            except asyncio.CancelledError:
                self.is_running = False
                break
            except Exception as e:
                print(f"WS error: {e}")
            finally:
                self.ws_connection = None
                self.state.hub_connected = False
                self.state.relay_connected = False
                self.state.sensor_connected = False
                self.state.update()

            if self.is_running:
                try:
                    await asyncio.sleep(5)
                except asyncio.CancelledError:
                    break

    async def toggle_relay(self, relay_on: bool):
        self.state.relay_state = relay_on
        if self.ws_connection and self.state.relay_connected:
            state_int = 1 if relay_on else 0
            try:
                await self.ws_connection.send(f"relay/set/{state_int}")
            except Exception as ex:
                print(f"Failed to send relay command: {ex}")
        self.state.update()

    async def request_history(self):
        if self.ws_connection:
            try:
                await self.ws_connection.send("history/get")
            except Exception as ex:
                print(f"Failed to request history: {ex}")
