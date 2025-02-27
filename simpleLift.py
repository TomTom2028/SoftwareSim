# simple shit: one floor that spawns items. the vlm takes the tray down, and takes one of the tray
import random
from enum import Enum
import salabim as sim

from tower.TowerGenerator import TowerGenerator


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
            self.hold(self.get_picktime())
            goto_vlm.bay_status.set(BayStatus.IDLE)


    def get_picktime(self):
        return sim.Poisson(20).sample()

    def schedule_notification(self, notification):
        notification.enter(self.notification_queue)

class PickerNotification(sim.Component):
    def __init__(self, vlm):
        super().__init__()
        self.vlm = vlm
    def process(self):
        self.passivate()



class OrderGenerator(sim.Component):
    def __init__(self, vlms, avg_amount_of_items):
        super().__init__()
        self.vlms = vlms
        self.avg_amount_of_items = avg_amount_of_items


    def assemble_random_order(self):
        item_count_dicts = [vlm.get_items_count() for vlm in self.vlms]
        item_dict = {}
        for item_count_dict in item_count_dicts:
            for item in item_count_dict:
                if item in item_dict:
                    item_dict[item] += item_count_dict[item]
                else:
                    item_dict[item] = item_count_dict[item]
        order_items = {}
        amount_of_items = sim.Poisson(self.avg_amount_of_items).sample()
        total_amount_items_left = 0
        for item in item_dict:
            total_amount_items_left += item_dict[item]

        while amount_of_items > 0 and total_amount_items_left > 0:
            item = random.choice(list(item_dict.keys()))
            amount = random.randint(1, total_amount_items_left)
            if item in order_items:
                order_items[item] += amount
            else:
                order_items[item] = amount
            amount_of_items -= amount
            total_amount_items_left -= amount
        return Order(order_items)


    def process(self):
        while True:
            # take a random vlm
            random_vlm = random.choice(self.vlms)
            order = Order(sim.Uniform(0, 10).sample())
            random_vlm.schedule(order)
            self.hold(sim.Uniform(10, 50).sample())




class Order(sim.Component):
    def __init__(self, items):
        super().__init__()
        self.items = items
    def process(self):
        self.passivate()


#vlm takes order out of the queue
class Vlm(sim.Component):


    def __init__(self, target_floor_number, speed, loading_time, picker, location, tower, vlm_name):
        super().__init__()
        self.target_floor_number = target_floor_number
        self.current_floor_number = target_floor_number
        self.loading_time = loading_time
        self.speed = speed
        self.picker = picker
        self.vlm_name = vlm_name
        self.location = location

        self.bay_status = sim.State(f'{vlm_name}_bay', value=BayStatus.IDLE)
        self.order_queue = sim.Queue(f'{vlm_name}_orderQueue')

        self.tower = tower

    def process(self):
        while True:
            while len(self.order_queue) == 0:
                self.standby()
            current_order = self.order_queue.pop()
            hold_time = get_time(self.current_floor_number, current_order.floor_number, self.speed)
            self.hold(hold_time)
            self.current_floor_number = current_order.floor_number
            self.hold(self.loading_time) # robot loading time
            self.hold(hold_time)
            self.current_floor_number = 0 # back to zero

            self.bay_status.set(BayStatus.READY)
            # we give the order to the picker
            self.picker.schedule_notification(PickerNotification(self))

            self.wait((self.bay_status, BayStatus.IDLE))
    def schedule(self, order):
        self.order_queue.add(order)


env = sim.Environment(trace=True)
person = Person("Person1")
vlmOne = Vlm(0, 1, 10, person, 0, [[]], "VlmOne")
vlmTwo = Vlm(0, 1, 10, person, 10, [[]], "VlmTwo")
OrderGenerator([vlmOne, vlmTwo], 2)




towerGenerator = TowerGenerator()
towerOne = towerGenerator.get_tower(10, 2, 20, "TowerOne")
# print tower
for level in towerOne:
    for Tray in level:
        content = Tray.content
        print(content)
"""

env.run(till=5000)
vlmOne.order_queue.length.print_histogram(30, 0, 1)
print()
vlmOne.order_queue.length_of_stay.print_histogram(30, 0, 10)
print('\n')
vlmTwo.order_queue.length.print_histogram(30, 0, 1)
print()
vlmTwo.order_queue.length_of_stay.print_histogram(30, 0, 10)
"""