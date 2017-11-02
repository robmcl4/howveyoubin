"""
howveyoubin.py

simulates the lettuce inventory-management system
"""

import sys

import script_parser
import reactor


# initial number of bins
INITIAL_BINS = 1

# seed
RAND_SEED = 1

# average service time, seconds
SERVICE_TIME = 0.05


def main():
    script_name = sys.argv[1]
    script = script_parser.parse_script(script_name)
    rctr = reactor.Reactor(0, INITIAL_BINS, 0, SERVICE_TIME, RAND_SEED)
    requests_serviced = 0
    time_spent_serving = 0
    for item in script:
        if isinstance(item, script_parser.InventoryRestock):
            rctr.add_stock(item.quantity, item.timestamp)
        elif isinstance(item, script_parser.InventoryRequest):
            completed_time, bin_id, qty = rctr.reserve_stock(
                item.quantity,
                item.timestamp
            )
            if qty != item.quantity:
                print('could not reserve enough inventory!!!', qty, bin_id)
                raise Exception()
            else:
                print('whoo', requests_serviced)
            elapsed = completed_time - item.timestamp
            time_spent_serving += elapsed
            requests_serviced += 1
    print('average service time', time_spent_serving / requests_serviced)

main()
