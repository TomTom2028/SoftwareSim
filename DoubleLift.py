import salabim as sim
from tower import Level
from tower.Tray import Tray
from Other import *
from Person import *
from VLM import *


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
        if (len(self.instruction_queue) > 1):
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
            if abs(self.lift_low_pos.get() - self.lift_low_orders[0].floor_number) > abs(
                    self.lift_high_pos.get() - self.lift_high_orders[0].floor_number):
                delta = abs(self.lift_low_pos.get() - self.lift_low_orders[0].floor_number)
            else:
                delta = abs(self.lift_high_pos.get() - self.lift_high_orders[0].floor_number)

            travel_time = delta / self.speed
            # Verplaats naar de bestemmingen
            self.hold(travel_time)
            self.lift_high_pos.set(self.lift_high_orders[0].floor_number)
            self.lift_low_pos.set(self.lift_low_orders[0].floor_number)

            # TODO: actually pickup
            # we "pick up" the thing
            self.hold(self.loading_time)

            # Naar pickingstation
            # hoogste zal altijd langste tijd moeten afleggen.
            self.state = sim.State("Action", value="Delivery")
            self.hold(self.lift_high_orders[0].floor_number / self.speed)
            self.lift_high_pos.set(0)
            self.lift_low_pos.set(-1)

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
            self.lift_high_pos.set(1)
            self.lift_low_pos.set(0)

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

            self.lift_high_pos.set(self.lift_high_orders[0].floor_number)
            self.lift_low_pos.set(self.lift_low_orders[0].floor_number)

            # plaats bak terug
            self.hold(self.loading_time)

            order = self.lift_high_orders.pop(0)
            order.activate()
            order = self.lift_low_orders.pop(0)
            order.activate()
        elif len(self.instruction_queue) == 1:
            #TODO fix beter
            self.state = sim.State("Action", value="Fetching")
            instruction = self.instruction_queue.pop()
            tray = instruction.tray
            self.in_transit_tray = tray
            self.bay_status.set(BayStatus.READY)
            self.picker.schedule_notification(PickerNotification(self, instruction.fetch_dict))

            self.wait((self.bay_status, BayStatus.IDLE))

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

