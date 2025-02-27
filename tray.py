import salabim as sim
class Tray(sim.Component):
    def __init__(self, name, initial_content=None):
        super().__init__()
        if initial_content is None:
            initial_content = {}
        self.content = initial_content
        self.name = name
    def process(self):
        self.passivate()

    def add_item(self, item):
        if (item_name := item.name) in self.content:
            self.content[item_name] += 1
        else:
            self.content[item_name] = 1

    def get_item_count(self, item):
        return self.content.get(item, 0)

    def remove_item(self, item):
        if (item_name := item.name) in self.content:
            self.content[item_name] -= 1
            if self.content[item_name] == 0:
                del self.content[item_name]
        else:
            raise ValueError("Item not in tray")