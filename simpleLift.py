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



class InternalVLMInstruction(sim.Component):
    def __init__(self, tray, fetch_dict: dict[str, int]):
        super().__init__()
        self.tray = tray
        self.fetch_dict = fetch_dict
    def process(self):
        self.passivate()


class DoubleLift(sim.Component):
    def __init__(self, speed, loading_time, picker, location, levels: [Level], vlm_name):
        super().__init__()


        self.lift_high_orders = []
        self.lift_low_orders = []


        self.state = sim.State("Action", value="Waiting")
        self.loading_time = loading_time
        self.speed = speed
        self.picker = picker
        self.location = location

        self.bay_status = sim.State(f'{vlm_name}_bay', value=BayStatus.IDLE)
        self.order_queue = sim.Queue(f'{vlm_name}_orderQueue')
        

        self.levels = levels
        self.high_in_transit_tray: None or Tray = None
        self.low_in_transit_tray: None or Tray = None

        self.lift_high_pos = sim.State(f"{vlm_name}_high_pos", value=0)
        self.lift_low_pos = sim.State(f"{vlm_name}_low_pos", value=-1)

        self.in_transit_tray: None or Tray = None #TODO: rename


        self.instruction_queue = sim.Queue(f'{vlm_name}_instruction_queue')


    def schedule(self, order):
        self.order_queue.add(order)

    def process(self):
        while True:
            while len(self.order_queue) == 0:
                self.standby()
            # each level can only be once in the instruction queue
            # this makes sure both lifts can't take both levels
            for order in self.order_queue:
                process_next_order = False
                while not process_next_order:
                    instruction = self.gen_vlm_instruction(order, self.get_blacklisted_trays())
                    if instruction is None:
                        process_next_order = True
                    else:
                        self.instruction_queue.add(instruction)
                        # also reserve the items
                        for item in instruction.fetch_dict:
                            order.order_items[item] -= instruction.fetch_dict[item]
                            instruction.tray.reserve_items(instruction.fetch_dict)
                            if order.order_items[item] == 0:
                                del order.order_items[item]
                if is_item_order_empty:
                    self.order_queue.remove(order)
            # the queue is empty or full of uselss orders, so standby
            self.process_instructionqueue()
            self.state = sim.State("Action", value="Waiting")
            self.standby()


        self.process_order()

    def get_blacklisted_trays(self):
        # go trough the instruction queue and get all the trays
        # in transit trays are already included
        trays = []
        for instruction in self.instruction_queue:
            trays.append(instruction.tray)
        # add all the levels
        level_trays_blacklisted = []
        for tray in trays:
            level = self.get_tray_level(tray)
            if level is not None:
                for bay in level.bays:
                    if bay.tray is not None and bay.tray not in level_trays_blacklisted and bay.tray not in trays:
                        level_trays_blacklisted.append(bay.tray)
        return trays + level_trays_blacklisted


    
    # TODO: make it so that one lift can operate if no more orders are queued
    # and there is only one item in the queue
    # TODO: make it so that a instruction can come from a lift on this order
    # a mock verison of this fn is below
    def process_instructionqueue_TOFIX(self):
        if (len(self.instruction_queue) < 2):
            return
        self.state = sim.State("Action", value="Fetching")
        self.order_one = None # instruction_queue.pop()
        self.order_two = None #instruction_queue.pop()
        if self.order_two.floor_number < self.order_one.floor_number:
            self.lift_high_orders.append(self.order_one)
            self.lift_low_orders.append(self.order_two)
        elif self.order_one.floor_number < self.order_two.floor_number:
            self.lift_high_orders.append(self.order_two)
            self.lift_low_orders.append(self.order_one)
        else:
            raise Exception("it broke")
            self.order_two.floor_number = self.order_two.floor_number - 1  # TODO fix
            self.lift_low_orders.append(self.order_two)
            self.lift_high_orders.append(self.order_one)

        # Langste tijd want de andere lift kan geen voorsprong nemen aangezien bij het afladen
        # steeds op de andere gewacht moet worden
        # Bereken langste afstand tussen lift en bestemming
        if abs(lift_low_pos.get() - self.lift_low_orders[0].floor_number) > abs(
                lift_high_pos.get() - self.lift_high_orders[0].floor_number):
            delta = abs(lift_low_pos.get() - self.lift_low_orders[0].floor_number)
        else:
            delta = abs(lift_high_pos.get() - self.lift_high_orders[0].floor_number)

        travel_time = delta / self.speed
        # Verplaats naar de bestemmingen
        self.hold(travel_time)
        lift_high_pos.set(self.lift_high_orders[0].floor_number)
        lift_low_pos.set(self.lift_low_orders[0].floor_number)

        # TODO: actually pickup
        # we "pick up" the thing
        self.hold(self.loading_time)

        # Naar pickingstation
        # hoogste zal altijd langste tijd moeten afleggen.
        self.state = sim.State("Action", value="Delivery")
        self.hold(self.lift_high_orders[0].floor_number / self.speed)
        lift_high_pos.set(0)
        lift_low_pos.set(-1)

        # unloading high in picking bay
        self.hold(self.loading_time)

        # picking door picker
        self.state = sim.State("Action", value="Picking")
        self.hold(self.picker.get_picktime)

        # reload bakske high
        self.hold(self.loading_time)

        # verplaatsen low en high 1 naar boven
        self.state = sim.State("Action", value="Delivery")
        self.hold(1 / self.speed)
        lift_high_pos.set(1)
        lift_low_pos.set(0)

        # load bakske low
        ld_time_in = self.loading_time
        self.hold(ld_time_in)

        # picking door picker
        self.state = sim.State("Action", value="Picking")
        pick_time = self.picker.get_picktime()
        self.hold(pick_time)

        # reload bakske low
        ld_time_out = self.loading_time
        self.hold(ld_time_out)

        self.state = sim.State("Action", value="Return")

        # Als het langer duurt voor de onderste op locatie te komen dan wachten we daar op anders wachten we op de bovenste.
        # Ook hier heeft het geen zin om voorsprong tenemen we wachten sws op de onderste lift.
        if ld_time_out + ld_time_in + pick_time + self.lift_low_orders[0].floor_number / self.speed > (
                self.lift_high_orders[0].floor_number - 1) / self.speed:
            self.hold(self.lift_low_orders[0].floor_number / self.speed)  # starts from 0
        else:
            self.hold((self.lift_high_orders[0].floor_number - 1) / self.speed)

        lift_high_pos.set(self.lift_high_orders[0].floor_number)
        lift_low_pos.set(self.lift_low_orders[0].floor_number)

        # plaats bak terug
        self.hold(self.loading_time)

        order = self.lift_high_orders.pop(0)
        order.activate()
        order = self.lift_low_orders.pop(0)
        order.activate()

        # Cyclus herbegint
    # returns the height of the tray and the level or null
    
    def process_instructionqueue(self):
        if len(self.instruction_queue) == 0:
            return
        self.state = sim.State("Action", value="Fetching")
        while len(self.instruction_queue) > 0:
            instruction = self.instruction_queue.pop()
            tray = instruction.tray
            self.in_transit_tray = tray
            self.bay_status.set(BayStatus.READY)
            self.picker.schedule_notification(PickerNotification(self, instruction.fetch_dict))

            self.wait((self.bay_status, BayStatus.IDLE))

            


        # TODO: make it here so multple item types can be fetched.
    def gen_vlm_instruction(self, order: VlmItemOrder, blacklist: [Tray]):
        trays = self.get_all_trays()
        for tray in trays:
            if tray in blacklist:
                continue
            items_in_tray = tray.get_items_count()
            for order_item in order.order_items:
                if order_item in items_in_tray and items_in_tray[order_item] > 0 and order.order_items[order_item] > 0:
                    return InternalVLMInstruction(tray, {order_item: min(order.order_items[order_item], items_in_tray[order_item])})
        return None

    def find_tray(self, tray):
        if self.high_in_transit_tray == tray:
            return self.lift_high_pos.get(), None
        if self.low_in_transit_tray == tray:
            return self.lift_low_pos.get(), None
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
        if self.high_in_transit_tray is not None:
            trays.append(self.high_in_transit_tray)
        if self.low_in_transit_tray is not None:
            trays.append(self.low_in_transit_tray)
        return trays

    def get_tray_level(self, tray):
        for level in self.levels:
            for bay in level.bays:
                if bay.tray == tray:
                    return level
        return None
    def get_corrected_items_count(self):
        # add everything in the trays
        to_return_items_count: dict[str, int] = {}
        for tray in self.get_all_trays():
            for item_name, item_count in tray.get_items_count().items():
                if item_name in to_return_items_count:
                    to_return_items_count[item_name] += item_count
                else:
                    to_return_items_count[item_name] = item_count
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






env.run(till=10000)
print(f"Length of order queues: {len(vlmOne.order_queue)} {len(vlmTwo.order_queue)}")
vlmOne.order_queue.length.print_histogram(30, 0, 1)
print()
vlmOne.order_queue.length_of_stay.print_histogram(30, 0, 10)
print('\n')
vlmTwo.order_queue.length.print_histogram(30, 0, 1)
print()
vlmTwo.order_queue.length_of_stay.print_histogram(30, 0, 10)