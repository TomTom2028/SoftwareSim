import salabim as sim
class Bay(sim.Component):
    def __init__(self, bay_name, tray):
        super().__init__()
        self.bay_name = bay_name
        self.tray = tray
    def process(self):
        self.passivate()
    def set_tray(self, tray):
        if self.tray is not None:
            raise ValueError("Tray already set")
        self.tray = tray

    def remove_tray(self):
        if self.tray is None:
            raise ValueError("No tray to remove")
        self.tray = None

    def is_empty(self):
        return self.tray is None
