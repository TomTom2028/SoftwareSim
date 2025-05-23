import salabim as sim
from Other import *
from GraphicsSettings import *

class Person(sim.Component):
    def __init__(self, person_name, timelog_array, env: sim.Environment, start_location, start_gui_location):
        super().__init__()
        self.person_name = person_name
        self.notification_queue = sim.Queue(f'{person_name}_notiQueue')
        self.current_location = start_location
        self.current_gui_location = start_gui_location
        self.rect = None
        self.timelog_array = timelog_array
        self.env = env
        self.is_walking = False
        self.update_rect()

    def update_rect(self):
        if self.rect is not None:
            self.rect.remove()
        self.rect = sim.AnimateRectangle(
            spec=(self.current_gui_location * MULTIPLIER, 0, self.current_gui_location * MULTIPLIER + 20, 20),
            fillcolor="purple" if self.is_walking else "orange", layer=-2, text=self.person_name)
        self.rect.show()


    def get_person_walking_time(self, delta):
        return abs(delta) * 0.5

    def process(self):
        while True:
            while len(self.notification_queue) == 0:
                self.standby()
            current_notification = self.notification_queue.pop()
            goto_vlm = current_notification.vlm
            self.is_walking = True
            self.update_rect()
            self.hold(self.get_person_walking_time(self.current_location - goto_vlm.location))
            self.current_location = goto_vlm.location
            self.current_gui_location = goto_vlm.gui_location
            self.is_walking = False
            self.update_rect()
            self.update_rect()
            self.wait((goto_vlm.bay_status, BayStatus.READY))
            self.timelog_array.append(self.env.now())
            for item_name, amount in current_notification.to_pick_items.items():
                self.hold(self.get_picktime())
                #goto_vlm.docked_tray.remove_item(item_name, amount)
            goto_vlm.bay_status.set(BayStatus.IDLE)
            self.update_rect()

    def get_picktime(self):
        return sim.Normal(10.81, 0.96).sample()

    def schedule_notification(self, notification):
        notification.enter(self.notification_queue)

class PickerNotification(sim.Component):
    def __init__(self, vlm, to_pick_items):
        super().__init__()
        self.vlm = vlm
        self.to_pick_items = to_pick_items
    def process(self):
        self.passivate()