# simple shit: one floor that spawns items. the lift takes the tray down, and takes one of the tray
import salabim as sim


class Person(sim.Component):
    def get_picktime(self):
        return sim.Poisson(20).sample()


class OrderGenerator(sim.Component):
    def process(self):
        while True:
            Order(int(sim.Uniform(1, 10).sample()))
            Order(int(sim.Uniform(1, 10).sample()))
            self.hold(sim.Uniform(20, 100).sample())


class Order(sim.Component):
    def __init__(self, floor_number):
        super().__init__()
        self.floor_number = floor_number

    def process(self):
        self.enter(orderQueue)
        self.passivate()


# lift takes order out of the queue
class Lift(sim.Component):
    def __init__(self, target_floor_number, speed, loading_time, picker):
        super().__init__()
        self.target_floor_number = target_floor_number
        self.current_floor_number = target_floor_number
        self.loading_time = loading_time
        self.speed = self.speed = speed
        self.picker = picker

    def process(self):
        while True:
            while len(orderQueue) == 0:
                self.standby()
            current_order = orderQueue.pop()
            delta = abs(self.current_floor_number - current_order.floor_number)
            hold_time = delta / self.speed
            self.hold(hold_time)
            self.current_floor_number = current_order.floor_number
            # TODO: actually pickup
            # we "pick up" the thing
            self.hold(self.loading_time)  # robot loading time
            self.hold(hold_time)
            self.current_floor_number = 0  # back to zero
            self.hold(self.picker.get_picktime)


class DoubleLift(sim.Component):
    def __init__(self, speed, loading_time, picker):
        super().__init__()
        self.lift_high_orders = []
        self.lift_low_orders = []
        self.state = sim.State("Action", value="Waiting")
        self.loading_time = loading_time
        self.speed = self.speed = speed
        self.picker = picker

    def process(self):
        lift_high_pos = sim.State("lift_high_pos", value=0)
        lift_low_pos = sim.State("lift_low_pos", value=-1)
        while True:
            while len(orderQueue) < 2:
                self.state = sim.State("Action", value="Waiting")
                self.standby()
            
            self.state = sim.State("Action", value="Fetching")
            self.order_one = orderQueue.pop()
            self.order_two = orderQueue.pop()
            if self.order_two.floor_number < self.order_one.floor_number:
                self.lift_high_orders.append(self.order_one)
                self.lift_low_orders.append(self.order_two)
            elif self.order_one.floor_number < self.order_two.floor_number:
                self.lift_high_orders.append(self.order_two)
                self.lift_low_orders.append(self.order_one)
            else:
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


env = sim.Environment(trace=True)
orderQueue = sim.Queue('orderQueue')
person = Person()
# Lift(1, 10, person)
DoubleLift(1, 10, person)
OrderGenerator()

env.run(till=5000)
orderQueue.length.print_histogram(30, 0, 1)
print()
orderQueue.length_of_stay.print_histogram(30, 0, 10)
