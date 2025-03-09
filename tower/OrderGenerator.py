import random

POSSIBLE_ITEMS = ["I-phone", "Orange", "Lenovo Laptop", "Water bottle", "Parker pen", "Wallet",
                  "Sunglasses", "Headphones", "Book", "T-shirt", "Jeans", "Shoes", "Watch", "Bracelet",
                  "Necklace", "Ring", "Earrings", "Perfume", "Lipstick", "Mascara", "Foundation", "Blush", ]
class OrderGenerator:
    def generate_pre_orders(self, amount_of_orders):
        orders = []
        for i in range(amount_of_orders):
            order = self.get_random_order(f"Order_{i}")
            orders.append(order)
        return orders

    def get_random_order(self, name):
        initial_content = {}
        for item in POSSIBLE_ITEMS:
            if random.random() < 0.5:
                initial_content[item] = random.randint(1, 10)
        return  initial_content
