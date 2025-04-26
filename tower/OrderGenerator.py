import random
import pickle

POSSIBLE_ITEMS = ["I-phone", "Orange", "Lenovo Laptop", "Water bottle", "Parker pen", "Wallet",
                  "Sunglasses", "Headphones", "Book", "T-shirt", "Jeans", "Shoes", "Watch", "Bracelet",
                  "Necklace", "Ring", "Earrings", "Perfume", "Lipstick", "Mascara", "Foundation", "Blush", ]
chance_dict = {}
with open('chance_dict.pkl', 'rb') as f:
    chance_dict = pickle.load(f)

chance_dict_keys = list(chance_dict.keys())

class OrderGenerator:
    def generate_pre_orders(self, amount_of_orders):
        orders = []
        for i in range(amount_of_orders):
            order = self.get_random_order(f"Order_{i}")
            orders.append(order)
        return orders

    def get_random_order(self, name):
        amount_of_items = 20 # TODO: randomize!
        order_flat = []
        first_item = random.choice(chance_dict_keys)
        order_flat.append(first_item)
        for i in range(amount_of_items - 1):
            random_item_from_order = random.choice(order_flat)
            chances_for_next_item = chance_dict.get(random_item_from_order)
            next_item = random.choices(list(chances_for_next_item.keys()), weights=chances_for_next_item.values())[0]
            order_flat.append(next_item)
        # conver to a dict
        order_dict = {}
        unique_items = list(set(order_flat))
        for item in unique_items:
            order_dict[item] = order_flat.count(item)
        return order_dict

