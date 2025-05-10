import pickle
import random

from scipy.stats import gamma

params = [1.62404227, 0.02906306, 4.05409424]
def gamma_pdf(x, alpha, beta, mult):
    return gamma.pdf(x, a=alpha, scale=1/beta) * mult

def gamma_wrapper(x):
    return gamma_pdf(x, *params)

chance_dict = {}
with open('tray_chance_dict.pkl', 'rb') as f:
    chance_dict = pickle.load(f)
chance_dict_keys = list(chance_dict.keys())

min_amount_tray = 0
max_amount_tray = 200
choices = [i for i in range(min_amount_tray, max_amount_tray + 1)]
weights = [gamma_wrapper(i) for i in choices]
weights /= sum(weights)
def get_random_amount():
    return random.choices(choices, weights=weights, k=1)[0]

def tray_filler():
    amount = get_random_amount()
    tray_flat = []
    first_item = random.choice(chance_dict_keys)
    tray_flat.append(first_item)
    for i in range(amount - 1):
        random_item_from_tray = random.choice(tray_flat)
        chances_for_next_item = chance_dict.get(random_item_from_tray)
        next_item = random.choices(list(chances_for_next_item.keys()), weights=chances_for_next_item.values())[0]
        tray_flat.append(next_item)
    tray_dict = {}
    unique_items = list(set(tray_flat))
    for item in unique_items:
        tray_dict[item] = tray_flat.count(item)
    return tray_dict



def vlm_filler(vlms):
    for vlm in vlms:
        for level in vlm.levels:
            for bay in level.bays:
                bay.tray.content = tray_filler()


def create_item_dict(item_names: list[str], avg_amount: int, min_amount: int):
    items = {}
    for item in item_names:
        items[item] = random.randint(min_amount, avg_amount * 2)
    return items