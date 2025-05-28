# simple shit: one floor that spawns items. the vlm takes the tray down, and takes one of the tray
import random
import time
import numpy as np

import salabim as sim

random.seed(time.time())


from tower.OrderGenerator import OrderGenerator
from tower.TowerGenerator import TowerGenerator
from tower.VlmUtilities import vlm_filler, create_item_dict
from DoubleLift import DoubleLift
from Other import VlmItemOrder
from Person import *

class OrderQueuer(sim.Component):
    def __init__(self, vlms, avg_amount_of_items, arbiter, orders):
        super().__init__()
        self.vlms = vlms
        self.avg_amount_of_items = avg_amount_of_items
        self.arbiter = arbiter
        self.orders = orders

    def process(self):
        while True:
            # take a random vlm
            print("VLM CONTENTS")
            for vlm in self.vlms:
                print(vlm.get_corrected_items_count())
           # take the first order
            current_order = self.orders.pop(0)
            print("ORDER", current_order)
            self.arbiter.schedule(current_order)
            self.hold(sim.Uniform(1, 2).sample())
            if (len(self.orders) == 0):
                return



class Arbiter:
    def __init__(self, vlms, bad_item_dict: dict[str, int]):
        self.vlms = vlms
        self.bad_item_dict = bad_item_dict
    # NOTE: it is not really important in what order the VLMS themself process the sets
    # TODO: make this somewhat smart
    def schedule(self, order_items: dict[str, int]):
        np.random.shuffle(self.vlms)
        item_orders_per_vlm = [{} for _ in self.vlms]
        vlm_corrected_items_count = [vlm.get_corrected_items_count() for vlm in self.vlms]
        for item in order_items:
            needed_amount = order_items[item]
            for idx, item_count in enumerate(vlm_corrected_items_count):
                if needed_amount == 0:
                    break
                if item in item_count:
                    to_take = min(needed_amount, max(item_count[item], 0))
                    if to_take == 0:
                        continue
                    needed_amount -= to_take
                    item_orders_per_vlm[idx][item] = to_take
            if needed_amount != 0:
                print(item, needed_amount)
                if item not in self.bad_item_dict:
                    self.bad_item_dict[item] = needed_amount
                else:
                    self.bad_item_dict[item] += needed_amount
                order_items[item] = 0

        # push the items trough to the vlm
        for idx, item_order in enumerate(item_orders_per_vlm):
            self.vlms[idx].schedule(VlmItemOrder(item_order))


orderGenerator = OrderGenerator()
orders = orderGenerator.generate_pre_orders(500)
combinedItems = {}
for order in orders:
    for item in order:
        if item in combinedItems:
            combinedItems[item] += order[item]
        else:
            combinedItems[item] = order[item]
print(orders)
print(combinedItems)

env = sim.Environment(trace=True)
list_for_logging = []
person = Person("Person1", list_for_logging, env, 4, 20)
towerGenerator = TowerGenerator()
towerOne = towerGenerator.get_tower(9, 2,  "VlmOne", 20)
towerTwo = towerGenerator.get_tower(9, 2,  "VlmTwo", 40)
#vlmOne = Vlm(0, 1, 10, person, 0, towerOne, "VlmOne")
#vlmTwo = Vlm(0, 1, 10, person, 10, towerTwo, "VlmTwo")
# DER IS IETS MIS ALS VLM 1 locatie 30 is en VLM2 locatie 10
vlmOne = DoubleLift(4.8, person, 4, 20, towerOne, "VlmOne")
vlmTwo = DoubleLift(4.8, person,8, 40, towerTwo, "VlmTwo")
vlm_filler([
    vlmOne,
   vlmTwo
])
# print the items in the system
print("ITEMS IN SYSTEM")
print(vlmOne.get_corrected_items_count())
print(vlmTwo.get_corrected_items_count())


badItemDict = {}
arbiter = Arbiter([vlmOne,
                   vlmTwo
                   ], badItemDict)
OrderQueuer([vlmOne,
             vlmTwo
             ], 2, arbiter, orders)


#env.animate(True)





env.run(till=1000000)
print(f"Length of order queues: {len(vlmOne.order_queue)} {len(vlmTwo.order_queue)}")
for order in vlmOne.order_queue:
    print(f"VlmOne: {order.order_items}")

for order in vlmTwo.order_queue:
    print(f"VlmTwo: {order.order_items}")

print("Total amount of items not in the system: ")
print(badItemDict)


vlmOne.order_queue.length.print_histogram(30, 0, 1)
print()
vlmOne.order_queue.length_of_stay.print_histogram(30, 0, 10)
print('\n')
vlmTwo.order_queue.length.print_histogram(30, 0, 1)
print()
vlmTwo.order_queue.length_of_stay.print_histogram(30, 0, 10)

print("##### LARGE LOGGING LIST #####")
#print(list_for_logging)


import numpy as np
import matplotlib.pyplot as plt

# Example data

delta_times = []
for i in range(1, len(list_for_logging)):
    delta_times.append(list_for_logging[i] - list_for_logging[i-1])
delta_times.sort()
print(delta_times)
per_second_times = [1/d_t for d_t in delta_times if d_t != 0]  # Avoid division by zero
# average time per second
average_time_per_second = np.mean(per_second_times)
average_time_per_hour = average_time_per_second * 3600
print(f"Average amount of processed items per hour: {average_time_per_hour:.2f}")

# Create histogram
plt.hist(delta_times, bins=60, alpha=0.7, color='blue', edgecolor='black')

# Add title and labels
plt.title("Histogram of Data")
plt.xlabel("Value")
plt.ylabel("Frequency")

# Show plot
plt.show()