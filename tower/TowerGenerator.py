import random

from tower.Tray import Tray
from tower.Level import Level

class TowerGenerator:
    POSSIBLE_ITEMS = ["I-phone", "Orange", "Lenovo Laptop", "Water bottle", "Parker pen", "Wallet",
                      "Sunglasses", "Headphones", "Book", "T-shirt", "Jeans", "Shoes", "Watch", "Bracelet",
                      "Necklace", "Ring", "Earrings", "Perfume", "Lipstick", "Mascara", "Foundation", "Blush",]


    def get_tower(self, amount_of_levels, trays_per_level, vlm_name):
        levels = []
        tray_counter = 0
        for i in range(amount_of_levels):
            level = Level(i, f"Level_{i}", trays_per_level)
            for j in range(trays_per_level):
                tray = self.get_random_tray(f"{vlm_name}_{tray_counter}")
                tray_counter += 1
                level.slot_tray(tray)
            levels.append(level)
        return levels

    def get_random_tray(self, name):
        initial_content = {}

        return Tray(name, initial_content)


