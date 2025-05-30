import random

import numpy as np
import salabim as sim
from Other import *
from GraphicsSettings import *
from scipy.stats import gamma

lambda_param = 1.67974217e-01
def exp_transform(x):
    return (-1/lambda_param) * np.log(x)

def gen_sample():
    return exp_transform(random.random())
#print(gen_sample())


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

    def process(self):
        while True:
            while len(self.notification_queue) == 0:
                self.standby()
            current_notification = self.notification_queue.pop()
            goto_vlm = current_notification.vlm
            self.is_walking = True
            self.update_rect()
            self.hold(self.get_walk_time(self.current_location, goto_vlm.location))
            self.current_location = goto_vlm.location
            self.current_gui_location = goto_vlm.gui_location
            self.is_walking = False
            self.update_rect()
            self.update_rect()
            self.wait((goto_vlm.bay_status, BayStatus.READY))
            self.timelog_array.append(self.env.now())
            hold_time = 0
            for _, amount in current_notification.to_pick_items.items():
                for i in range(amount):
                   hold_time += self.get_picktime()
            self.hold(hold_time)
            goto_vlm.bay_status.set(BayStatus.IDLE)
            self.update_rect()

    def get_picktime(self):
        return gen_sample()
        #return sim.Normal(10.81, 0.96).sample()

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