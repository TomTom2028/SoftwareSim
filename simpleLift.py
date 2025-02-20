# simple shit: one floor that spawns items. the lift takes the tray down, and takes one of the tray
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
            goto_lift = current_notification.lift
            self.hold(get_time(self.current_location, goto_lift.location, 0.5))
            self.current_location = goto_lift.location
            self.hold(self.get_picktime())
            goto_lift.bay_status.set(BayStatus.IDLE)


    def get_picktime(self):
        return sim.Poisson(20).sample()

    def schedule_notification(self, notification):
        notification.enter(self.notification_queue)


class OrderGenerator(sim.Component):
    def process(self):
        while True:
            Order(sim.Uniform(0, 10).sample())
            self.hold(sim.Uniform(20, 100).sample())


class PickerNotification(sim.Component):
    def __init__(self, lift):
        super().__init__()
        self.lift = lift
    def process(self):
        self.passivate()

class Order(sim.Component):
    def __init__(self, floor_number):
        super().__init__()
        self.floor_number = floor_number
    def process(self):
        self.enter(orderQueue)
        self.passivate()


#lift takes order out of the queue
class Lift(sim.Component):
    def __init__(self, target_floor_number, speed, loading_time, picker, location, lift_name):
        super().__init__()
        self.target_floor_number = target_floor_number
        self.current_floor_number = target_floor_number
        self.loading_time = loading_time
        self.speed = speed
        self.picker = picker
        self.lift_name = lift_name
        self.location = location

        self.bay_status = sim.State(f'{lift_name}_bay', value=BayStatus.IDLE)

    def process(self):
        while True:
            while len(orderQueue) == 0:
                self.standby()
            current_order = orderQueue.pop()
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




env = sim.Environment(trace=True)
orderQueue = sim.Queue('orderQueue')
person = Person("Person1")
Lift(0, 1, 10, person, 0, "LiftOne")
OrderGenerator()

env.run(till=5000)
orderQueue.length.print_histogram(30, 0, 1)
print()
orderQueue.length_of_stay.print_histogram(30, 0, 10)
