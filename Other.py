from enum import Enum
import salabim as sim


class VlmItemOrder(sim.Component):
    def __init__(self ,order_items: dict[str, int]):
        super().__init__()
        self.order_items = order_items
    def process(self):
        self.passivate()

    def absorb(self, other):
        for item in other.order_items:
            if item in self.order_items:
                self.order_items[item] += other.order_items[item]
            else:
                self.order_items[item] = other.order_items[item]

#vlm takes order out of the queue
def is_item_order_empty(order: VlmItemOrder):
    for item in order.order_items:
        if order.order_items[item] > 0:
            return False
    return True

class BayStatus(Enum):
    IDLE = "IDLE"
    READY = "READY"


def get_time(a, b, speed):
    return abs(a - b)/speed