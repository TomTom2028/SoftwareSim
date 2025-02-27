# simple shit: one floor that spawns items. the vlm takes the tray down, and takes one of the tray
import random
from enum import Enum
import salabim as sim
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
    def __init__(self, vlms):
        super().__init__()
        self.vlms = vlms
    def process(self):
        while True:
            # take a random vlm
            random_vlm = random.choice(self.vlms)
            order = Order(sim.Uniform(0, 10).sample())
            random_vlm.schedule(order)
            self.hold(sim.Uniform(10, 50).sample())




class Order(sim.Component):
    def __init__(self, floor_number):
        super().__init__()
        self.floor_number = floor_number
    def process(self):
        self.passivate()


#vlm takes order out of the queue
class Vlm(sim.Component):
    def __init__(self, target_floor_number, speed, loading_time, picker, location, vlm_name):
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
vlmOne = Vlm(0, 1, 10, person, 0, "VlmOne")
vlmTwo = Vlm(0, 1, 10, person, 10, "VlmTwo")
OrderGenerator([vlmOne, vlmTwo])

env.run(till=5000)
vlmOne.order_queue.length.print_histogram(30, 0, 1)
print()
vlmOne.order_queue.length_of_stay.print_histogram(30, 0, 10)
print('\n')
vlmTwo.order_queue.length.print_histogram(30, 0, 1)
print()
vlmTwo.order_queue.length_of_stay.print_histogram(30, 0, 10)
