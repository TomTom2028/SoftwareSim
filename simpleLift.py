# simple shit: one floor that spawns items. the vlm takes the tray down, and takes one of the tray
import salabim as sim

from tower.OrderGenerator import OrderGenerator
from tower.TowerGenerator import TowerGenerator
from tower.VlmUtilities import vlm_filler
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
            self.hold(sim.Uniform(10, 50).sample())
            if (len(self.orders) == 0):
                return



class Arbiter:
    def __init__(self, vlms):
        self.vlms = vlms
    # NOTE: it is not really important in what order the VLMS themself process the sets
    # TODO: make this somewhat smart
    def schedule(self, order_items: dict[str, int]):
        item_orders_per_vlm = [{} for _ in self.vlms]
        vlm_corrected_items_count = [vlm.get_corrected_items_count() for vlm in self.vlms]
        for item in order_items:
            needed_amount = order_items[item]
            for idx, item_count in enumerate(vlm_corrected_items_count):
                if needed_amount == 0:
                    break
                if item in item_count:
                    to_take = min(needed_amount, item_count[item])
                    if to_take == 0:
                        continue
                    needed_amount -= to_take
                    item_orders_per_vlm[idx][item] = to_take
            if needed_amount != 0:
                print(item, needed_amount)
                raise ValueError("Not enough items in the system")

        # push the items trough to the vlm
        for idx, item_order in enumerate(item_orders_per_vlm):
            self.vlms[idx].schedule(VlmItemOrder(item_order))


orderGenerator = OrderGenerator()
orders = orderGenerator.generate_pre_orders(30)
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
person = Person("Person1")
towerGenerator = TowerGenerator()
towerOne = towerGenerator.get_tower(7, 2,  "VlmOne")
towerTwo = towerGenerator.get_tower(7, 2,  "VlmTwo")
#vlmOne = Vlm(0, 1, 10, person, 0, towerOne, "VlmOne")
#vlmTwo = Vlm(0, 1, 10, person, 10, towerTwo, "VlmTwo")
vlmOne = DoubleLift(1, 10, person, 10, towerTwo, "VlmTwo")
vlmTwo = DoubleLift(1, 10, person, 0, towerOne, "VlmOne")
vlm_filler([vlmOne, vlmTwo], combinedItems)
# print the items in the system
print("ITEMS IN SYSTEM")
print(vlmOne.get_corrected_items_count())
print(vlmTwo.get_corrected_items_count())



arbiter = Arbiter([vlmOne, vlmTwo])
OrderQueuer([vlmOne, vlmTwo], 2, arbiter, orders)






env.run(till=100000)
print(f"Length of order queues: {len(vlmOne.order_queue)} {len(vlmTwo.order_queue)}")
for order in vlmOne.order_queue:
    print(f"VlmOne: {order.order_items}")

for order in vlmTwo.order_queue:
    print(f"VlmTwo: {order.order_items}")
vlmOne.order_queue.length.print_histogram(30, 0, 1)
print()
vlmOne.order_queue.length_of_stay.print_histogram(30, 0, 10)
print('\n')
vlmTwo.order_queue.length.print_histogram(30, 0, 1)
print()
vlmTwo.order_queue.length_of_stay.print_histogram(30, 0, 10)