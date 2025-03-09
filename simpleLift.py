# simple shit: one floor that spawns items. the vlm takes the tray down, and takes one of the tray
import random
from enum import Enum
import salabim as sim

from tower import Level
from tower.OrderGenerator import OrderGenerator
from tower.TowerGenerator import TowerGenerator
from tower.VlmUtilities import vlm_filler
from tower.Tray import Tray


class BayStatus(Enum):
    IDLE = "IDLE"
    READY = "READY"


def get_time(a, b, speed):
    return abs(a - b)/speed

class Person(sim.Component):
    def __init__(self, person_name):
        super().__init__()
        self.person_name = person_name
        self.notification_queue = sim.Queue(f'{person_name}_notiQueue')
        self.current_location = 0

    def process(self):
        while True:
            while len(self.notification_queue) == 0:
                self.standby()
            current_notification = self.notification_queue.pop()
            goto_vlm = current_notification.vlm
            self.hold(get_time(self.current_location, goto_vlm.location, 0.5))
            self.current_location = goto_vlm.location
            for item_name, amount in current_notification.to_pick_items.items():
                self.hold(self.get_picktime())
                goto_vlm.in_transit_tray.remove_item(item_name, amount)
            goto_vlm.bay_status.set(BayStatus.IDLE)


    def get_picktime(self):
        return sim.Poisson(20).sample()

    def schedule_notification(self, notification):
        notification.enter(self.notification_queue)

class PickerNotification(sim.Component):
    def __init__(self, vlm, to_pick_items):
        super().__init__()
        self.vlm = vlm
        self.to_pick_items = to_pick_items
    def process(self):
        self.passivate()



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




class VlmItemOrder(sim.Component):
    def __init__(self ,order_items: dict[str, int]):
        super().__init__()
        self.order_items = order_items
    def process(self):
        self.passivate()

    def absorb(self, other):
        for item in other.order_items:
            if item in self.order_items:
                self.order_items[item] += other.order_items[item]
            else:
                self.order_items[item] = other.order_items[item]



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







#vlm takes order out of the queue
def is_item_order_empty(order: VlmItemOrder):
    for item in order.order_items:
        if order.order_items[item] > 0:
            return False
    return True


class Vlm(sim.Component):
    levels: [Level]

    def __init__(self, target_floor_number, speed, loading_time, picker, location, levels: [Level], vlm_name):
        super().__init__()
        self.current_floor_number = target_floor_number
        self.loading_time = loading_time
        self.speed = speed
        self.picker = picker
        self.vlm_name = vlm_name
        self.location = location

        self.bay_status = sim.State(f'{vlm_name}_bay', value=BayStatus.IDLE)
        self.order_queue = sim.Queue(f'{vlm_name}_orderQueue')

        self.levels = levels
        self.current_order = None
        self.in_transit_tray: None or Tray = None

    def process(self):
        while True:
            while len(self.order_queue) == 0:
                self.standby()
            self.current_order = self.order_queue.pop()
            self.process_order()


    #processes the current  order
    def process_order(self):
        while not is_item_order_empty(self.current_order):
            tray, item, amount_to_take = self.get_tray_for_part_of_order(self.current_order)
            if amount_to_take == 0:
                raise ValueError("This should not happen")
            tray.reserve_items({item: amount_to_take})
            # remove the items form the order
            self.current_order.order_items[item] -= amount_to_take
            height, level = self.find_tray(tray)
            if level is None:
                raise ValueError("In this iteration of the program the bay should be put back!")
            # go to the tray
            hold_time = get_time(self.current_floor_number, height, self.speed)
            self.hold(hold_time)
            self.current_floor_number = height
            level.get_tray(tray.tray_name)
            self.in_transit_tray = tray
            self.hold(self.loading_time) # robot loading time
            hold_time = get_time(self.current_floor_number, 0, self.speed)
            self.hold(hold_time) # go down time
            self.bay_status.set(BayStatus.READY)
            self.picker.schedule_notification(PickerNotification(self, {item: amount_to_take}))

            self.wait((self.bay_status, BayStatus.IDLE))
            # put the tray back
            hold_time = get_time(self.current_floor_number, height, self.speed)
            self.hold(hold_time)
            level.slot_tray(tray)
            self.in_transit_tray = None
            self.hold(self.loading_time)  # robot loading time
        self.current_order = None

    def schedule(self, order):
        self.order_queue.add(order)


    # returns tuple of tray, item, amount_to_take
    def get_tray_for_part_of_order(self, order: VlmItemOrder):
        trays = self.get_all_trays()
        for tray in trays:
            items_in_tray = tray.get_items_count()
            for order_item in order.order_items:
                if order_item in items_in_tray and items_in_tray[order_item] > 0 and order.order_items[order_item] > 0:
                    return tray, order_item, min(order.order_items[order_item], items_in_tray[order_item])
        raise ValueError("No tray found")

    # returns the height of the tray and the level or null
    def find_tray(self, tray):
        if self.in_transit_tray == tray:
            return self.current_floor_number, None
        for level in self.levels:
            for bay in level.bays:
                if bay.tray == tray:
                    return self.current_floor_number, level
        raise ValueError("No tray found")



    def get_all_trays(self):
        trays = []
        for level in self.levels:
            for bay in level.bays:
                if bay.tray is not None:
                    trays.append(bay.tray)
        if self.in_transit_tray is not None:
            trays.append(self.in_transit_tray)
        return trays


    def get_all_orders(self):
        orders = []
        for order in self.order_queue:
            orders.append(order)
        if self.current_order is not None:
            orders.append(self.current_order)
        return orders

    def get_corrected_items_count(self)->dict[str, int]:
        to_return_items_count: dict[str, int] = {}

        for tray in self.get_all_trays():
            for item_name, item_count in tray.get_items_count().items():
                if item_name in to_return_items_count:
                    to_return_items_count[item_name] += item_count
                else:
                    to_return_items_count[item_name] = item_count

        for order in self.get_all_orders():
            for item_name, item_count in order.order_items.items():
                if item_name not in to_return_items_count and item_count == 0: # this is allowed and answer should be null, just continue
                    continue
                if item_name in to_return_items_count:
                    if (to_return_items_count[item_name] - item_count) < 0:
                        raise ValueError("Not enough items in the system")
                    to_return_items_count[item_name] -= item_count
                else:
                    raise ValueError("Item not in system")
        return to_return_items_count


orderGenerator = OrderGenerator()
orders = orderGenerator.generate_pre_orders(18)
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
vlmOne = Vlm(0, 1, 10, person, 0, towerOne, "VlmOne")
vlmTwo = Vlm(0, 1, 10, person, 10, towerTwo, "VlmTwo")
vlm_filler([vlmOne, vlmTwo], combinedItems)
# print the items in the system
print("ITEMS IN SYSTEM")
print(vlmOne.get_corrected_items_count())
print(vlmTwo.get_corrected_items_count())



arbiter = Arbiter([vlmOne, vlmTwo])
OrderQueuer([vlmOne, vlmTwo], 2, arbiter, orders)






env.run(till=10000)
print(f"Length of order queues: {len(vlmOne.order_queue)} {len(vlmTwo.order_queue)}")
vlmOne.order_queue.length.print_histogram(30, 0, 1)
print()
vlmOne.order_queue.length_of_stay.print_histogram(30, 0, 10)
print('\n')
vlmTwo.order_queue.length.print_histogram(30, 0, 1)
print()
vlmTwo.order_queue.length_of_stay.print_histogram(30, 0, 10)