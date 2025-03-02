import salabim as sim

from tower.Bay import Bay


class Level(sim.Component):
    def __init__(self, level_name, amount_of_bays):
        super().__init__()
        self.level_name = level_name
        self.bays = [Bay(f"{level_name}_bay_{i}", None) for i in range(amount_of_bays)]
    def process(self):
        self.passivate()

    def slot_tray(self, tray):
        for bay in self.bays:
            if bay.is_empty():
                bay.set_tray(tray)
                return
        raise ValueError("No empty bays")
    def get_tray(self, tray_name):
        for bay in self.bays:
            if bay.tray.tray_name == tray_name:
                return bay.remove_tray()
        raise ValueError("Tray not found")
    #TODO: figure out what to do with moving trays
    def get_items_count(self):
        items_dict = {}
        for bay in self.bays:
            if bay.tray is not None:
                for item_name, item_count in bay.tray.get_items_count().items():
                    if item_name in items_dict:
                        items_dict[item_name] += item_count
                    else:
                        items_dict[item_name] = item_count
        return items_dict