class AppState:
    def __init__(self):
        self.hub_connected = False
        self.relay_connected = False
        self.sensor_connected = False
        self.relay_state = False
        self.temp_val = "25"
        self.hum_val = "30"
        self.on_state_change = None

    def update(self):
        if self.on_state_change:
            self.on_state_change()
