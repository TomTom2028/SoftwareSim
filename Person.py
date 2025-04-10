import salabim as sim
from Other import *
from GraphicsSettings import *

class Person(sim.Component):
    def __init__(self, person_name):
        super().__init__()
        self.person_name = person_name
        self.notification_queue = sim.Queue(f'{person_name}_notiQueue')
        self.current_location = 0
        self.rect = None

    def update_rect(self):
        if self.rect is not None:
            self.rect.remove()
        self.rect = sim.AnimateRectangle(spec=(self.current_location * MULTIPLIER, 0, self.current_location * MULTIPLIER + 20, 20), fillcolor="orange", layer=-2, text=self.person_name)
        self.rect.show()

    def process(self):
        while True:
            while len(self.notification_queue) == 0:
                self.standby()
            current_notification = self.notification_queue.pop()
            goto_vlm = current_notification.vlm
            self.hold(get_time(self.current_location, goto_vlm.location, 0.5))
            self.current_location = goto_vlm.location
            self.update_rect()
            self.wait((goto_vlm.bay_status, BayStatus.READY))
            for item_name, amount in current_notification.to_pick_items.items():
                self.hold(self.get_picktime())
                goto_vlm.docked_tray.remove_item(item_name, amount)
            goto_vlm.bay_status.set(BayStatus.IDLE)
            self.update_rect()

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