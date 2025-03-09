import salabim as sim
class Tray(sim.Component):
    def __init__(self, name, initial_content=None):
        super().__init__()
        if initial_content is None:
            initial_content = {}
        self.content = initial_content
        self.reserved_content = {}
        self.tray_name = name
    def process(self):
        self.passivate()

    def add_item(self, item):
        if item in self.content:
            self.content[item] += 1
        else:
            self.content[item] = 1

    def add_items(self, item, amount):
        if item in self.content:
            self.content[item] += amount
        else:
            self.content[item] = amount

    def get_item_count(self, item):
        return self.content.get(item, 0) - self.reserved_content.get(item, 0)

    def get_items_count(self):
        correct_items_dict = {}
        for item_name in self.content:
            correct_items_dict[item_name] = self.get_item_count(item_name)
        return correct_items_dict


    def remove_item(self, item, amount):
        if item in self.content:
            self.content[item] -= amount
            if self.content[item] == 0:
                del self.content[item]
        else:
            raise ValueError("Item not in tray")
        if item in self.reserved_content:
            self.reserved_content[item] -= amount
            if self.reserved_content[item] == 0:
                del self.reserved_content[item]

    def reserve_items(self, items_dict):
        for item_name, item_count in items_dict.items():
            if item_name in self.content:
                if self.get_item_count(item_name) < 0:
                    raise ValueError("Not enough items in tray")
                if item_name in self.reserved_content:
                    self.reserved_content[item_name] += item_count
                else:
                    self.reserved_content[item_name] = item_count
            else:
                raise ValueError("Item not in tray")