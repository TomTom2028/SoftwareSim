import salabim as sim
# TODO: maybe just merge with the VLM! (not sure yet)
class Tower(sim.Component):
    def __init__(self, tower_name, levels):
        super().__init__()
        self.tower_name = tower_name
        self.levels = levels
    def process(self):
        self.passivate()
    def get_items_count(self):
        items_dict = {}
        for level in self.levels:
            for item_name, item_count in level.get_items_count().items():
                if item_name in items_dict:
                    items_dict[item_name] += item_count
                else:
                    items_dict[item_name] = item_count
        return items_dict