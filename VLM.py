from Other import VlmItemOrder, is_item_order_empty
import salabim as sim
from tower import Level
from tower.Tray import Tray
from Other import *
from Person import *


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
        self.docked_tray: None or Tray = None

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
            self.docked_tray = tray
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
            self.docked_tray = None
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
        if self.docked_tray == tray:
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
        if self.docked_tray is not None:
            trays.append(self.docked_tray)
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
    

class InternalVLMInstruction(sim.Component):
    def __init__(self, tray, fetch_dict: dict[str, int]):
        super().__init__()
        self.tray = tray
        self.fetch_dict = fetch_dict
    def process(self):
        self.passivate()
