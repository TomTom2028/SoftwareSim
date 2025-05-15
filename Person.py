import salabim as sim
from Other import *

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
            self.hold(self.get_walk_time(self.current_location, goto_vlm.location))
            self.current_location = goto_vlm.location
            for item_name, amount in current_notification.to_pick_items.items():
                self.hold(self.get_picktime())
                goto_vlm.docked_tray.remove_item(item_name, amount)
            goto_vlm.bay_status.set(BayStatus.IDLE)


    def get_picktime(self):
        return sim.Normal(10.81, 0.96).sample()

    def schedule_notification(self, notification):
        notification.enter(self.notification_queue)
    
    def get_walk_time(self, position, destination):
        speed = sim.Normal(1.39, 0.07).sample() #5km/h en 0.25km/h in m/s
        return abs(position - destination)/speed

class PickerNotification(sim.Component):
    def __init__(self, vlm, to_pick_items):
        super().__init__()
        self.vlm = vlm
        self.to_pick_items = to_pick_items
    def process(self):
        self.passivate()