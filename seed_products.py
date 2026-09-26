# adds the starter products to track. run once.
from db import add_product

starters = [
    (2290, "Redwick LED Strip Core", "Neutral white"),
    (2665, "Orbisk Dumbbell Set Duo", "Regular"),
    (2188, "Veloria Resistance Bands Edge", "Advanced"),
]

for item_id, name, option in starters:
    p = add_product(item_id, name, option)
    print("tracking:", p["name"], "-", p["option_label"])
