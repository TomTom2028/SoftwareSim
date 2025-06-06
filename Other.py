from enum import Enum
import salabim as sim
from math import pow


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


def get_time(a, b, speed=None):
    return time_calc(abs(a - b))
    #return 0
    #return abs(a - b)/speed
def get_time(delta, speed=None):
    return time_calc(abs(delta))

def time_calc(s_tot):
    s_tot = s_tot * (5 / 19)
    # should be part of the vlm at some point
    v_max = 0.6
    a_max = 1
    j_max = 20
    shape = -1
    v_max = 0.6

    v_a = (a_max*a_max/j_max)
    s_a = 2*pow(a_max, 3)/pow(j_max,2)
    s_v = v_max*((v_max/a_max)+a_max/j_max)

    if(s_tot<s_a):
        shape = 1
    elif(v_max<v_a):
        shape = 2
    elif(s_tot<s_v):
        shape = 3
    else:
        shape = 4

    match shape:
        case 1:
            return pow((s_tot/(2*j_max)), 1/3)
        case 2:
            return (s_tot/v_max - pow((v_max/j_max),0.5))
        case 3:
            t_j = a_max/j_max
            t_a1 = (4*s_tot*pow(j_max,2)+pow(a_max,3))/(a_max*pow(j_max,2))
            t_a2 = 3*a_max/j_max
            return t_j + 0.5*(pow(t_a1, 0.5)-t_a2)
        case 4:
            return s_tot/v_max + a_max/j_max
        case -1:
            exit(-1)
