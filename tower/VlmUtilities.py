import random
def vlm_filler(vlms, items: dict[str, int]):
    # go trough each item and get a random amount
    while len(items) > 0:
        random_item = random.choice(list(dict.keys(items)))
        random_amount = random.randint(1, items[random_item])
        # take a random vlm
        random_vlm = random.choice(vlms)
        # take a random level
        random_level = random.choice(random_vlm.levels)
        # take a random bay
        random_bay = random.choice(random_level.bays)
        # put it here
        random_bay.tray.add_items(random_item, random_amount)
        # decrement the amount of items
        items[random_item] -= random_amount
        # remove the item if there are no more left
        if items[random_item] == 0:
            del items[random_item]



def create_item_dict(item_names: list[str], avg_amount: int, min_amount: int):
    items = {}
    for item in item_names:
        items[item] = random.randint(min_amount, avg_amount * 2)
    return items