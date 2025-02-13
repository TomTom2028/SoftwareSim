# simple shit: one floor that spawns items. the lift takes the tray down, and takes one of the tray
import salabim as sim
class OrderGenerator(sim.Component):
    def process(self):
        while True:
            Order(sim.Uniform(0, 10).sample())
            self.hold(sim.Uniform(20, 100).sample())

class Order(sim.Component):
    def __init__(self, floor_number):
        super().__init__()
        self.floor_number = floor_number
    def process(self):
        self.enter(orderQueue)
        self.passivate()


#lift takes order out of the queue
class Lift(sim.Component):
    def __init__(self, target_floor_number, speed, pickup_time):
        super().__init__()
        self.target_floor_number = target_floor_number
        self.current_floor_number = target_floor_number
        self.pickup_time = pickup_time
        self.speed = self.speed = speed

    def process(self):
        while True:
            while len(orderQueue) == 0:
                self.standby()
            current_order = orderQueue.pop()
            delta = abs(self.current_floor_number - current_order.floor_number)
            hold_time = delta / self.speed
            self.hold(hold_time)
            self.current_floor_number = current_order.floor_number
            #TODO: actually pickup
            # we "pick up" the thing
            self.hold(30) # takeout time



env = sim.Environment(trace=True)
orderQueue = sim.Queue('orderQueue')
Lift(0)
OrderGenerator()

env.run(till=5000)
orderQueue.length.print_histogram(30, 0, 1)
print()
orderQueue.length_of_stay.print_histogram(30, 0, 10)
