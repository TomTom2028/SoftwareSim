# simple shit: one floor that spawns items. the vlm takes the tray down, and takes one of the tray
import random
import time
from multiprocessing import freeze_support

import salabim as sim

random.seed(time.time())


from tower.OrderGenerator import OrderGenerator
from tower.TowerGenerator import TowerGenerator
from tower.VlmUtilities import vlm_filler, create_item_dict
from DoubleLift import DoubleLift
from Other import VlmItemOrder
from Person import *

class OrderQueuer(sim.Component):
    def __init__(self, vlms, avg_amount_of_items, arbiter, orders):
        super().__init__()
        self.vlms = vlms
        self.avg_amount_of_items = avg_amount_of_items
        self.arbiter = arbiter
        self.orders = orders

    def process(self):
        while True:
            # take a random vlm
            print("VLM CONTENTS")
            for vlm in self.vlms:
                print(vlm.get_corrected_items_count())
           # take the first order
            current_order = self.orders.pop(0)
            print("ORDER", current_order)
            self.arbiter.schedule(current_order)
            self.hold(sim.Uniform(1, 2).sample())
            if (len(self.orders) == 0):
                return



class Arbiter:
    def __init__(self, vlms, bad_item_dict: dict[str, int]):
        self.vlms = vlms
        self.bad_item_dict = bad_item_dict
    # NOTE: it is not really important in what order the VLMS themself process the sets
    # TODO: make this somewhat smart
    def schedule(self, order_items: dict[str, int]):
        item_orders_per_vlm = [{} for _ in self.vlms]
        vlm_corrected_items_count = [vlm.get_corrected_items_count() for vlm in self.vlms]
        for item in order_items:
            needed_amount = order_items[item]
            for idx, item_count in enumerate(vlm_corrected_items_count):
                if needed_amount == 0:
                    break
                if item in item_count:
                    to_take = min(needed_amount, max(item_count[item], 0))
                    if to_take == 0:
                        continue
                    needed_amount -= to_take
                    item_orders_per_vlm[idx][item] = to_take
            if needed_amount != 0:
                print(item, needed_amount)
                if item not in self.bad_item_dict:
                    self.bad_item_dict[item] = needed_amount
                else:
                    self.bad_item_dict[item] += needed_amount
                order_items[item] = 0

        # push the items trough to the vlm
        for idx, item_order in enumerate(item_orders_per_vlm):
            self.vlms[idx].schedule(VlmItemOrder(item_order))



def old_main():
    orderGenerator = OrderGenerator()
    orders = orderGenerator.generate_pre_orders(500)
    combinedItems = {}
    for order in orders:
        for item in order:
            if item in combinedItems:
                combinedItems[item] += order[item]
            else:
                combinedItems[item] = order[item]
    print(orders)
    print(combinedItems)

    env = sim.Environment(trace=True)
    list_for_logging = []
    person = Person("Person1", list_for_logging, env, 4, 20)
    towerGenerator = TowerGenerator()
    towerOne = towerGenerator.get_tower(9, 2, "VlmOne", 20)
    towerTwo = towerGenerator.get_tower(9, 2, "VlmTwo", 40)
    # vlmOne = Vlm(0, 1, 10, person, 0, towerOne, "VlmOne")
    # vlmTwo = Vlm(0, 1, 10, person, 10, towerTwo, "VlmTwo")
    # DER IS IETS MIS ALS VLM 1 locatie 30 is en VLM2 locatie 10
    vlmOne = DoubleLift(4.8, person, 4, 20, towerOne, "VlmOne")
    vlmTwo = DoubleLift(4.8, person, 8, 40, towerTwo, "VlmTwo")
    vlm_filler([
        vlmOne,
        vlmTwo
    ])
    # print the items in the system
    print("ITEMS IN SYSTEM")
    print(vlmOne.get_corrected_items_count())
    print(vlmTwo.get_corrected_items_count())

    badItemDict = {}
    arbiter = Arbiter([vlmOne,
                       vlmTwo
                       ], badItemDict)
    OrderQueuer([vlmOne,
                 vlmTwo
                 ], 2, arbiter, orders)

    # env.animate(True)

    env.run(till=1000000)
    print(f"Length of order queues: {len(vlmOne.order_queue)} {len(vlmTwo.order_queue)}")
    for order in vlmOne.order_queue:
        print(f"VlmOne: {order.order_items}")

    for order in vlmTwo.order_queue:
        print(f"VlmTwo: {order.order_items}")

    print("Total amount of items not in the system: ")
    print(badItemDict)

    vlmOne.order_queue.length.print_histogram(30, 0, 1)
    print()
    vlmOne.order_queue.length_of_stay.print_histogram(30, 0, 10)
    print('\n')
    vlmTwo.order_queue.length.print_histogram(30, 0, 1)
    print()
    vlmTwo.order_queue.length_of_stay.print_histogram(30, 0, 10)

    print("##### LARGE LOGGING LIST #####")
    # print(list_for_logging)

    import numpy as np
    import matplotlib.pyplot as plt

    # Example data

    delta_times = []
    for i in range(1, len(list_for_logging)):
        delta_times.append(list_for_logging[i] - list_for_logging[i - 1])
    delta_times.sort()
    print(delta_times)
    per_second_times = [1 / d_t for d_t in delta_times if d_t != 0]  # Avoid division by zero
    # average time per second
    average_time_per_second = np.mean(per_second_times)
    average_time_per_hour = average_time_per_second * 3600
    print(f"Average amount of processed items per hour: {average_time_per_hour:.2f}")

    # Create histogram
    plt.hist(delta_times, bins=60, alpha=0.7, color='blue', edgecolor='black')

    # Add title and labels
    plt.title("Histogram of Data")
    plt.xlabel("Value")
    plt.ylabel("Frequency")

    # Show plot
    plt.show()






def run_test(has_two_vlms, one_lift_mode, distance_between_vlms=4):
    order_generator = OrderGenerator()
    orders = order_generator.generate_pre_orders(500)
    combined_items = {}
    for order in orders:
        for item in order:
            if item in combined_items:
                combined_items[item] += order[item]
            else:
                combined_items[item] = order[item]
    env = sim.Environment(trace=False)
    list_for_logging = []
    person = Person("Person1", list_for_logging, env, 4, 20)
    tower_generator = TowerGenerator()
    tower_one = tower_generator.get_tower(9, 2, "VlmOne", 20)
    tower_two = None
    vlm_two = None
    if has_two_vlms:
        tower_two = tower_generator.get_tower(9, 2, "VlmTwo", 40)
    vlm_one = DoubleLift(4.8, person, 4, 20, tower_one, "VlmOne", one_lift_mode=one_lift_mode)
    if has_two_vlms:
        vlm_two = DoubleLift(4.8, person, 4 +distance_between_vlms, 40, tower_two, "VlmTwo", one_lift_mode=one_lift_mode)
    if has_two_vlms:
        vlm_filler([
            vlm_one,
            vlm_two
        ])
    else:
        vlm_filler([vlm_one])

    # print the items in the system
    print("ITEMS IN SYSTEM")
    print(vlm_one.get_corrected_items_count())
    if has_two_vlms:
        print(vlm_two.get_corrected_items_count())
    bad_item_dict = {}
    arbiter = None
    if has_two_vlms:
        arbiter = Arbiter([vlm_one, vlm_two], bad_item_dict)
    else:
        arbiter = Arbiter([vlm_one], bad_item_dict)
    if has_two_vlms:
        order_queuer = OrderQueuer([vlm_one, vlm_two], 2, arbiter, orders)
    else:
        order_queuer = OrderQueuer([vlm_one], 2, arbiter, orders)
    env.run(till=1000000)
    if has_two_vlms:
        print(f"Length of order queues: {len(vlm_one.order_queue)} {len(vlm_two.order_queue)}")
    else:
        print(f"Length of order queues: {len(vlm_one.order_queue)}")
    for order in vlm_one.order_queue:
        print(f"VlmOne: {order.order_items}")
    if has_two_vlms:
        for order in vlm_two.order_queue:
            print(f"VlmTwo: {order.order_items}")

    print("Total amount of items not in the system: ")
    print(bad_item_dict)
    delta_times = []
    for i in range(1, len(list_for_logging)):
        delta_times.append(list_for_logging[i] - list_for_logging[i - 1])
    return delta_times

from concurrent.futures import ProcessPoolExecutor, as_completed

ONE_VLM_ONE_LIFT = (False, True, "One VLM, One Lift")
ONE_VLM_TWO_LIFTS = (False, False, "One VLM, Two Lifts")
TWO_VLMS_ONE_LIFT = (True, True, "Two VLMS, One Lift")
TWO_VLMS_TWO_LIFTS = (True, False, "Two VLMS, Two Lifts")

class TestCase:
    def __init__(self, has_two_vlms, one_lift_mode, name, distance_between_vlms=4.0):
        self.has_two_vlms = has_two_vlms
        self.one_lift_mode = one_lift_mode
        self.distance_between_vlms = distance_between_vlms
        self.name = name

all_testcass = [
    TestCase(*ONE_VLM_ONE_LIFT),
    TestCase(*ONE_VLM_TWO_LIFTS),
    TestCase(*TWO_VLMS_ONE_LIFT),
]




def run_parallel_tests(testcase: TestCase):
    total_delta_times = []
    two_vlms, one_lift_mode, description = testcase.has_two_vlms, testcase.one_lift_mode, testcase.name
    distance_between_vlms = testcase.distance_between_vlms
    with ProcessPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(run_test, two_vlms, one_lift_mode, distance_between_vlms) for _ in range(20)]
        for future in as_completed(futures):
            total_delta_times += future.result()
    total_delta_times.sort()
    return total_delta_times

import numpy as np
import matplotlib.pyplot as plt
import json
def runNormalTestCases():
    if __name__ == '__main__':
        freeze_support()
        for case in all_testcass:
            name = case.name
            print(f"Running test case: {name}")
            totalDeltaTimes = run_parallel_tests(case)
            print(f"Test case {name} completed with {len(totalDeltaTimes)} delta times.")
            # Print the average time per hour
            average_items_per_hour = None
            if len(totalDeltaTimes) > 0:
                average_time_per_second = np.mean(totalDeltaTimes)
                average_items_per_second = 1 / average_time_per_second if average_time_per_second > 0 else 0
                average_items_per_hour = average_items_per_second * 3600
                print(f"Average amount of processed items per hour for {name}: {average_items_per_hour:.2f}")
            else:
                average_items_per_hour = None
                print(f"No delta times recorded for {name}.")
            # json output
            json_blob = {
                "name": name,
                "delta_times": totalDeltaTimes,
                "average_items_per_hour": average_items_per_hour
            }
            with open(f"{name.replace(' ', '_').lower()}.json", 'w') as f:
                json.dump(json_blob, f, indent=4)
            # Create histogram
            plt.hist(totalDeltaTimes, bins=60, alpha=0.7, color='blue', edgecolor='black')
            # Add title and labels
            plt.title(f"Histogram of Delta Times for {name}")
            plt.xlabel("Delta Time (seconds)")
            plt.ylabel("Frequency")
            # plot to file
            plt.savefig(f"{name.replace(' ', '_').replace(',', '').lower()}.png")
            plt.close()  # Close the current figure




def runDistanceTestCases():
    if __name__ == '__main__':
        freeze_support()
        x_values = []
        y_values = []
        for distance in np.arange(2, 20, 0.5):
            #case = TestCase(True, False, f"Two VLMS, Two Lifts, Distance {distance}", distance)
            case = TestCase(True, True, f"Two VLMS, One Lift, Distance {distance}", distance)
            print(f"Running test case: {case.name}")
            x_values.append(distance)
            y_values.append(np.average(np.array(run_parallel_tests(case))))
        # Save the results to a JSON file
        json_blob = {
            "distances": x_values,
            "average_delta_times": y_values
        }
        with open("distance_test_results_1lift.json", 'w') as f:
            json.dump(json_blob, f, indent=4)
        # Create a plot
        plt.plot(x_values, y_values, marker='o')
        plt.title("Average Delta Times vs Distance Between VLMS")
        plt.xlabel("Distance Between VLMS (meters)")
        plt.ylabel("Average Delta Time (seconds)")
        plt.grid(True)
        plt.savefig("distance_test_results_1lift.png")
        plt.close()

#runNormalTestCases()
runDistanceTestCases()