# simple shit: one floor that spawns items. the vlm takes the tray down, and takes one of the tray
import numbers
import random
import time
from math import floor
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
    def __init__(self, vlms, avg_amount_of_items, arbiter, orders, do_print=False):
        super().__init__()
        self.vlms = vlms
        self.avg_amount_of_items = avg_amount_of_items
        self.arbiter = arbiter
        self.orders = orders
        self.do_print = do_print

    def process(self):
        while True:
            # take a random vlm
            if self.do_print:
                print("VLM CONTENTS")
                for vlm in self.vlms:
                    print(vlm.get_corrected_items_count())
           # take the first order
            current_order = self.orders.pop(0)
            if self.do_print:
                print("ORDER", current_order)
            self.arbiter.schedule(current_order)
            self.hold(sim.Uniform(1, 2).sample())
            if (len(self.orders) == 0):
                return



class Arbiter:
    def __init__(self, vlms, bad_item_dict: dict[str, int], do_print=False):
        self.vlms = vlms
        self.bad_item_dict = bad_item_dict
        self.do_print = do_print
    # NOTE: it is not really important in what order the VLMS themself process the sets
    # TODO: make this somewhat smart
    def schedule(self, order_items: dict[str, int]):
        random_vlms = random.sample(self.vlms, len(self.vlms))
        item_orders_per_vlm = [{} for _ in random_vlms]
        vlm_corrected_items_count = [vlm.get_corrected_items_count() for vlm in random_vlms]
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
                if self.do_print:
                    print(item, needed_amount)
                if item not in self.bad_item_dict:
                    self.bad_item_dict[item] = needed_amount
                else:
                    self.bad_item_dict[item] += needed_amount
                order_items[item] = 0

        # push the items trough to the vlm
        for idx, item_order in enumerate(item_orders_per_vlm):
            random_vlms[idx].schedule(VlmItemOrder(item_order))



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

class VlmTestSetting:
    def __init__(self,one_lift_mode: bool, location, amount_of_levels: int, name: str):
        self.one_lift_mode = one_lift_mode
        self.location = location
        self.amount_of_levels = amount_of_levels
        self.name = name
    def __str__(self):
        return f"VlmTestSetting(one_lift_mode={self.one_lift_mode}, location={self.location}, amount_of_levels={self.amount_of_levels}, name={self.name})"



def run_test(settings: [VlmTestSetting], do_print=False):
    order_generator = OrderGenerator()
    orders = order_generator.generate_pre_orders(250 * len(settings))
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
    vlms = []
    for current_setting in settings:
        current_tower = tower_generator.get_tower(current_setting.amount_of_levels, 2, current_setting.name, current_setting.location * 10)
        vlm = DoubleLift(4.8, person, current_setting.location, current_setting.location * 10, current_tower, current_setting.name, one_lift_mode=current_setting.one_lift_mode)
        vlms.append(vlm)

    vlm_filler(vlms)
    if do_print:
        # print the items in the system
        print("ITEMS IN SYSTEM")
        for vlm in vlms:
            print(vlm.get_corrected_items_count())


    bad_item_dict = {}
    arbiter = None
    arbiter = Arbiter(vlms, bad_item_dict)
    order_queuer = OrderQueuer(vlms, 2, arbiter, orders, do_print)
    env.run(till=1000000)
    if do_print:
        for vlm in vlms:
            print(f"VLM {vlm.name} order queue length: {len(vlm.order_queue)}")
            print(f"VLM {vlm.name} order queue items: {[order.order_items for order in vlm.order_queue]}")

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
    def __init__(self, settings: list[VlmTestSetting], name):
        self.settings = settings
        self.name = name

    def to_filename(self):
        return self.name.replace(' ', '_').replace(',', '').lower()


def create_case_one_vlm_one_lift():
    return TestCase([VlmTestSetting(True, 4, 9, "VLM_1")], "One VLM, One Lift")

def create_case_one_vlm_two_lifts():
    return TestCase([VlmTestSetting(False, 4, 9, "VLM_1")], "One VLM, Two Lifts")

def create_case_two_vlms_one_lift():
    return TestCase([VlmTestSetting(True, 4, 9, "VLM_1"),
                     VlmTestSetting(True, 8, 9, "VLM_2")], "Two VLMS, One Lift")

def create_case_two_vlms_two_lifts():
    return TestCase([VlmTestSetting(False, 4, 9, "VLM_1"),
                     VlmTestSetting(False, 8, 9, "VLM_2")], "Two VLMS, Two Lifts")

def create_case_two_vlms_onehalf_lift():
    return TestCase([VlmTestSetting(True, 4, 9, "VLM_1"),
                     VlmTestSetting(False, 8, 9, "VLM_2")], "Two VLMS, One and a Half Lift")


def create_distance_between_vlms_test_case(distance, one_lift: bool):
    return TestCase([
                VlmTestSetting(one_lift, 2, 9, "VLM_1"),
                VlmTestSetting(one_lift, 2 + distance, 9, "VLM_2")],
            f"Two VLMS, {'One' if one_lift else 'Two'} Lifts, Distance {distance}")



def create_amount_vlms_test_cases(amount_vlms: int, one_lift: bool):
    return TestCase([VlmTestSetting(one_lift, i * 2, 9, f"VLM_{i}") for i in range(amount_vlms)],
                    f"{amount_vlms} VLMS, {'One' if one_lift else 'Two'} Lifts")


def calculate_s(timing_values: list[float]):
    average = sum(timing_values) / len(timing_values)
    s_squared = sum((x - average) ** 2 for x in timing_values) / (len(timing_values) - 1)
    s = s_squared ** 0.5
    return s


def run_parallel_tests(testcase: TestCase, d_value = 0.5):
    total_delta_times = []
    average_delta_times = []
    max_workers = 8
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(run_test, testcase.settings, False) for _ in range(100)]
        for future in as_completed(futures):
            new_delta_times = future.result()
            total_delta_times += new_delta_times
            average_delta_times.append(sum(new_delta_times) / len(new_delta_times) if len(new_delta_times) > 0 else 0)
        print(f"Ran initial tests for {testcase.name}, got {len(total_delta_times)} delta times.")
        while calculate_s(average_delta_times) / (len(average_delta_times) ** 0.5) >= d_value:
            amount_of_extra_cases = min(max(floor(((calculate_s(average_delta_times)/ d_value) ** 2) - len(average_delta_times)), max_workers), 100)
            print(f"Running more tests for {testcase.name}, current d comparer: {calculate_s(average_delta_times) / (len(average_delta_times) ** 0.5) }")
            print(f"Extra runs: {amount_of_extra_cases}")
            futures = [executor.submit(run_test, testcase.settings, False) for _ in range(amount_of_extra_cases)]
            for future in as_completed(futures):
                new_delta_times = future.result()
                total_delta_times += new_delta_times
                average_delta_times.append(
                    sum(new_delta_times) / len(new_delta_times) if len(new_delta_times) > 0 else 0)
        print(f"Final s: {calculate_s(average_delta_times)} for {testcase.name}, with {len(average_delta_times)} runs.")

    total_delta_times.sort()
    return total_delta_times

import numpy as np
import matplotlib.pyplot as plt
import json

def generate_normal_testcases():
    return [
        create_case_one_vlm_one_lift(),
        create_case_one_vlm_two_lifts(),
        create_case_two_vlms_one_lift(),
        create_case_two_vlms_two_lifts(),
        create_case_two_vlms_onehalf_lift()
    ]


def runNormalTestCases():
    if __name__ == '__main__':
        all_testcases = generate_normal_testcases()
        for case in all_testcases:
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
            print("")
            # json output
            json_blob = {
                "name": name,
                "delta_times": totalDeltaTimes,
                "average_items_per_hour": average_items_per_hour
            }
            with open(f"output_tests/{case.to_filename()}.json", 'w') as f:
                json.dump(json_blob, f, indent=4)
            # Create histogram
            plt.hist(totalDeltaTimes, bins=60, alpha=0.7, color='blue', edgecolor='black')
            # Add title and labels
            plt.title(f"Histogram of Delta Times for {name}")
            plt.xlabel("Delta Time (seconds)")
            plt.ylabel("Frequency")
            # plot to file
            plt.savefig(f"output_tests/{case.to_filename()}.png")
            plt.close()  # Close the current figure




def runDistanceTestCases(one_lift_mode: bool):
    if __name__ == '__main__':
        x_values = []
        y_values = []

        for distance in np.arange(2, 20, 0.5):
            case = create_distance_between_vlms_test_case(distance, one_lift_mode)
            print(f"Running test case: {case.name}")
            x_values.append(distance)
            y_values.append(np.average(np.array(run_parallel_tests(case))))
        # Save the results to a JSON file
        json_blob = {
            "distances": x_values,
            "average_delta_times": y_values
        }
        file_name_base = "distance_test_results_1lift" if one_lift_mode else "distance_test_results_2lifts"
        with open(f"output_tests/{file_name_base}.json", 'w') as f:
            json.dump(json_blob, f, indent=4)
        # Create a plot
        plt.plot(x_values, y_values, marker='o')
        plt.title(f"Average Delta Times vs Distance Between VLMS ({'One lift' if one_lift_mode else 'Two lifts'})")
        plt.xlabel("Distance Between VLMS (meters)")
        plt.ylabel("Average Delta Time (seconds)")
        plt.grid(True)
        plt.savefig(f"output_tests/{file_name_base}.png")
        plt.close()

def runAmountVlmTestCases(one_lift_mode: bool):
    if __name__ == '__main__':
        x_values = []
        y_values = []

        for amount_vlms in np.arange(1, 20):
            case = create_amount_vlms_test_cases(amount_vlms, one_lift_mode)
            print(f"Running test case: {case.name}")
            x_values.append(amount_vlms)
            y_values.append(np.average(np.array(run_parallel_tests(case))))
        # Save the results to a JSON file
        json_blob = {
            "amount_vlms": x_values,
            "average_delta_times": y_values
        }
        file_name_base = "amount_vlms_results_1lift" if one_lift_mode else "amount_vlms_results_2lifts"
        with open(f"output_tests/{file_name_base}.json", 'w') as f:
            json.dump(json_blob, f, indent=4)
        # Create a plot
        plt.plot(x_values, y_values, marker='o')
        plt.title(f"Average Delta Times vs Amount VLMS ({'One lift' if one_lift_mode else 'Two lifts'})")
        plt.xlabel("Amount of VLMS")
        plt.ylabel("Average Delta Time (seconds)")
        plt.grid(True)
        plt.savefig(f"output_tests/{file_name_base}.png")
        plt.close()


if __name__ == '__main__':
    freeze_support()
runNormalTestCases()
runDistanceTestCases(True)
runDistanceTestCases(False)
runNormalTestCases(True)
runDistanceTestCases(False)