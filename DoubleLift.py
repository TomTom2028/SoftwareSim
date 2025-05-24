from typing import Any, Tuple

import salabim as sim

from GraphicsSettings import VLMTHICKNESS, LAYERHEIGHT, MULTIPLIER, BASE_Y
from tower import Level
from tower.Tray import Tray
from Other import *
from Person import *
from VLM import *


class DoubleLift(sim.Component):
    def __init__(self, loading_time, picker, location, gui_location, levels: [Level], vlm_name):
        super().__init__()

        self.all_tray_list = []

        self.vlm_name = vlm_name

        self.lift_high_instructions = []
        self.lift_low_instructions = []


        self.state = sim.State("Action", value="Waiting")
        self.loading_time = loading_time
        self.picker = picker
        self.location = location
        self.gui_location = gui_location

        self.bay_status = sim.State(f'{vlm_name}_bay', value=BayStatus.IDLE)
        self.order_queue = sim.Queue(f'{vlm_name}_orderQueue')
        

        self.levels = levels
        for level in self.levels:
            for bay in level.bays:
                if bay.tray is not None:
                    self.all_tray_list.append(bay.tray)
        self.high_in_transit_tray: None or Tray = None
        self.low_in_transit_tray: None or Tray = None

        self.lift_high_pos = sim.State(f"{vlm_name}_high_pos", value=0)
        self.lift_low_pos = sim.State(f"{vlm_name}_low_pos", value=-1)

        self.in_transit_tray_high: None or Tray = None #TODO: rename
        self.in_transit_tray_low: None or Tray = None #TODO: rename


        self.instruction_queue = sim.Queue(f'{vlm_name}_instruction_queue')
        self.docked_tray: Tray = None
        self.rect = sim.AnimateRectangle(spec=((self.gui_location - VLMTHICKNESS / 2) * MULTIPLIER, BASE_Y, (self.gui_location + VLMTHICKNESS / 2) * MULTIPLIER, len(self.levels) * LAYERHEIGHT + BASE_Y), fillcolor="blue" ,text=self.vlm_name, layer=0)
        self._rect_height = None
        self._rect_low = None

    def update_rects(self):
        if self._rect_height is not None:
            self._rect_height.remove()
        if self._rect_low is not None:
            self._rect_low.remove()
        self._rect_height = sim.AnimateRectangle(
            spec=((self.gui_location - VLMTHICKNESS / 2) * MULTIPLIER, (self.lift_high_pos.get() + 1) * LAYERHEIGHT, (self.gui_location + VLMTHICKNESS / 2) * MULTIPLIER, (self.lift_high_pos.get() + 2) * LAYERHEIGHT), fillcolor="green", layer=-1, text=self.in_transit_tray_high.tray_name if self.in_transit_tray_high is not None else "None")
        self._rect_low = sim.AnimateRectangle(spec=((self.gui_location - VLMTHICKNESS / 2) * MULTIPLIER, (self.lift_low_pos.get() + 1) * LAYERHEIGHT, (self.gui_location + VLMTHICKNESS / 2) * MULTIPLIER, (self.lift_low_pos.get() + 2) * LAYERHEIGHT), fillcolor="green", layer=-1, text=self.in_transit_tray_low.tray_name if self.in_transit_tray_low is not None else "None")
        self._rect_height.show()
        self._rect_low.show()



    def schedule(self, order):
        self.order_queue.add(order)

    def process(self):
        while True:
            while len(self.order_queue) == 0 and len(self.instruction_queue) == 0:
                self.standby()
            # each level can only be once in the instruction queue
            # this makes sure both lifts can't take both levels
            removed_orders = []
            for i in range(len(self.order_queue)):
                order = self.order_queue[i]
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
                            instruction.tray.content[item] -= instruction.fetch_dict[item]
                            #instruction.tray.reserve_items(instruction.fetch_dict)
                            if order.order_items[item] == 0:
                                del order.order_items[item]
                if is_item_order_empty(order):
                    removed_orders.append(order)
            #self.order_queue[i] = order
            # the queue is empty or full of uselss orders, so standby
            self.process_instructionqueue_TOFIX()
            self.state = sim.State("Action", value="Waiting")
            for order in removed_orders:
                self.order_queue.remove(order)

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
            self.instruction_one = self.instruction_queue.pop() # instruction_queue.pop()
            self.instruction_two = self.instruction_queue.pop() #instruction_queue.pop()
            tray_one_lvl = self.find_tray(self.instruction_one.tray)
            tray_two_lvl = self.find_tray(self.instruction_two.tray)
            tray_one_lvl.get_tray(self.instruction_one.tray.tray_name)
            tray_two_lvl.get_tray(self.instruction_two.tray.tray_name)
            if tray_two_lvl.get() < tray_one_lvl.get():
                self.lift_high_instructions.append(self.instruction_one)
                tray_high = self.instruction_one.tray
                self.lift_low_instructions.append(self.instruction_two)
                tray_low = self.instruction_two.tray
                tray_high_lvl = tray_one_lvl.get()
                tray_low_lvl = tray_two_lvl.get()
            elif tray_one_lvl.get() < tray_two_lvl.get():
                self.lift_high_instructions.append(self.instruction_two)
                tray_high = self.instruction_two.tray
                self.lift_low_instructions.append(self.instruction_one)
                tray_low = self.instruction_one.tray
                tray_high_lvl = tray_two_lvl.get()
                tray_low_lvl = tray_one_lvl.get()
            else:
                raise Exception("it broke")
                self.order_two.floor_number = self.order_two.floor_number - 1  # TODO fix
                self.lift_low_instructions.append(self.instruction_two)
                self.lift_high_instructions.append(self.instruction_one)

            self.in_transit_tray_high = tray_high
            self.in_transit_tray_low = tray_low
            self.update_rects()


            # Langste tijd want de andere lift kan geen voorsprong nemen aangezien bij het afladen
            # steeds op de andere gewacht moet worden
            # Bereken langste afstand tussen lift en bestemming
            if abs(self.lift_low_pos.get() - tray_low_lvl) > abs(
                    self.lift_high_pos.get() - tray_high_lvl):
                delta = abs(self.lift_low_pos.get() - tray_low_lvl)
            else:
                delta = abs(self.lift_high_pos.get() - tray_high_lvl)

            # Verplaats naar de bestemmingen
            self.hold(get_time(delta))
            self.lift_high_pos.set(tray_high_lvl)
            self.lift_low_pos.set(tray_low_lvl)
            self.update_rects()

            # TODO: actually pickup
            # we "pick up" the thing
            self.hold(self.loading_time)

            # Naar pickingstation
            # hoogste zal altijd langste tijd moeten afleggen.
            self.state = sim.State("Action", value="Delivery")
            self.hold(get_time(tray_high_lvl))
            self.lift_high_pos.set(0)
            self.lift_low_pos.set(-1)
            self.docked_tray = self.in_transit_tray_high

            self.update_rects()
            # unloading high in picking bay
            self.hold(self.loading_time)

            # picking door picker
            self.state = sim.State("Action", value="Picking")
            self.bay_status.set(BayStatus.READY)
            self.picker.schedule_notification(PickerNotification(self, self.lift_high_instructions[0].fetch_dict))
            self.wait((self.bay_status, BayStatus.IDLE))


            # reload bakske high
            self.hold(self.loading_time)

            # verplaatsen low en high 1 naar boven
            self.state = sim.State("Action", value="Delivery")
            self.hold(get_time(1))
            self.lift_high_pos.set(1)
            self.lift_low_pos.set(0)
            self.docked_tray = self.in_transit_tray_low
            self.update_rects()
            # load bakske low
            ld_time_in = self.loading_time
            self.hold(ld_time_in)

            # picking door picker
            self.state = sim.State("Action", value="Picking")
            self.bay_status.set(BayStatus.READY)
            self.picker.schedule_notification(PickerNotification(self, self.lift_low_instructions[0].fetch_dict))
            self.wait((self.bay_status, BayStatus.IDLE))

            # reload bakske low
            ld_time_out = self.loading_time
            self.hold(ld_time_out)

            self.state = sim.State("Action", value="Return")

            # Als het langer duurt voor de onderste op locatie te komen dan wachten we daar op anders wachten we op de bovenste.
            # Ook hier heeft het geen zin om voorsprong tenemen we wachten sws op de onderste lift.
            if ld_time_out + ld_time_in + get_time(tray_low_lvl) > get_time(
                    tray_high_lvl - 1):
                self.hold(get_time(tray_low_lvl))  # starts from 0
            else:
                self.hold(get_time(tray_high_lvl))
            self.docked_tray = None

            self.lift_high_pos.set(tray_high_lvl)
            self.lift_low_pos.set(tray_low_lvl)
            self.update_rects()
            self.in_transit_tray_high = None
            self.in_transit_tray_low = None

            # plaats bak terug
            self.hold(self.loading_time)

            tray_one_lvl.slot_tray(self.instruction_one.tray)
            tray_two_lvl.slot_tray(self.instruction_two.tray)
            self.update_rects()

            order = self.lift_high_instructions.pop(0)
            order.activate()
            order = self.lift_low_instructions.pop(0)
            order.activate()

        elif len(self.instruction_queue) == 1:
            #tray, item, amount_to_take = self.get_tray_for_part_of_order(self.current_order)
            self.instruction_one = self.instruction_queue.pop()
            self.lift_low_instructions.append(self.instruction_one)
            tray = self.instruction_one.tray
            # remove the items form the order
            level = self.find_tray(tray)
            if level is None:
                raise ValueError("In this iteration of the program the bay should be put back!")
            # go to the tray
            hold_time = get_time(self.lift_low_pos.get(), level.get())
            self.hold(hold_time)
            level.get_tray(tray.tray_name)

            self.lift_low_pos.set(level.get())
            self.lift_high_pos.set(level.get() +1)
            self.in_transit_tray_low = tray
            self.update_rects()
            self.hold(self.loading_time) # robot loading time
            hold_time = get_time(self.lift_low_pos.get(), 0)
            self.hold(hold_time) # go down time
            self.lift_low_pos.set(0)
            self.lift_high_pos.set(1)
            self.docked_tray = self.in_transit_tray_low
            self.bay_status.set(BayStatus.READY)
            self.picker.schedule_notification(PickerNotification(self, self.lift_low_instructions[0].fetch_dict))
            self.update_rects()
            self.wait((self.bay_status, BayStatus.IDLE))
            # put the tray back
            hold_time = get_time(self.lift_low_pos.get(), level.get())
            self.hold(hold_time)
            self.lift_low_pos.set(level.get())
            level.slot_tray(tray)
            self.in_transit_tray_low = None
            self.docked_tray =None
            self.update_rects()
            self.hold(self.loading_time)  # robot loading time

        # Cyclus herbegint
    # returns the height of the tray and the level or null
    
    def process_instructionqueue(self):
        if len(self.instruction_queue) == 0:
            return
        self.state = sim.State("Action", value="Fetching")
        while len(self.instruction_queue) > 0:
            instruction = self.instruction_queue.pop()
            tray = instruction.tray
            self.docked_tray = tray
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
                    items_in_tray
                    return InternalVLMInstruction(tray, {order_item: min(order.order_items[order_item], items_in_tray[order_item])})
        return None

    def find_tray(self, tray) -> Level:
        if self.high_in_transit_tray == tray:
            return None
        if self.low_in_transit_tray == tray:
            return None
        for level in self.levels:
            for bay in level.bays:
                if bay.tray == tray:
                    return level
        raise ValueError("No tray found")



    def get_all_trays(self):
        return self.all_tray_list
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
        # get all items in order queue and subtract them!
        for order in self.order_queue:
            for item_name, item_count in order.order_items.items():
                if item_name in to_return_items_count:
                    to_return_items_count[item_name] -= item_count
                else:
                    to_return_items_count[item_name] = -item_count
        return to_return_items_count
