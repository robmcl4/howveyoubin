#!/usr/bin/python3
"""
howveyoubin.py

simulates the lettuce inventory-management system
"""

import argparse
import numpy as np
import matplotlib.pyplot as plt

import script_parser
import reactor


# initial number of bins
INITIAL_BINS = 400

# seed
RAND_SEED = 1

# average service time, seconds
SERVICE_TIME = 0.05


def perform_experiment(num_bins, filename):
    """
    Performs the experiment given the supplied number of bins.
    Returns (avg service time, success rate) as floats from 0 to 1
    """
    script_name = filename
    script = script_parser.parse_script(script_name)
    rctr = reactor.Reactor(0, num_bins, 0, SERVICE_TIME, RAND_SEED)
    requests_serviced = 0
    failed_requests = 0
    time_spent_serving = 0

    #
    # The record of currently-in-progress requests. Requests are put here
    # when they need to look into another bin (or restock),
    # but potentially need to yield to another thread in the meantime.
    # This should be kept sorted by next action
    # timestamp.
    # [(InventoryRequest, quantity_reserved_so_far, next_bin_to_check,
    #   first_bin_checked, time_to_execute)
    #   OR
    #  (None, quantity_to_return, None, None, time_to_execute)]
    requests_in_progress = []

    # iterate while there's still work to do
    while len(requests_in_progress) > 0 or len(script) > 0:
        # find out whether we should continue executing an inventory request
        # or execute a new item
        if len(requests_in_progress) > 0 and (
                len(script) == 0 or
                requests_in_progress[0][4] <= script[0].timestamp ):
            # we should continue a request (or do a restock)
            inv_req, reserved_so_far, next_bin_to_check, \
                first_bin_checked, time_to_execute = requests_in_progress[0]
            del requests_in_progress[0]
            # if restock:
            if inv_req == None:
                rctr.add_stock(reserved_so_far, time_to_execute)
            # if request:
            else:
                completed_time, bin_id, qty = rctr.reserve_stock(
                    inv_req.quantity - reserved_so_far,
                    time_to_execute
                )
                assert inv_req.quantity >= qty + reserved_so_far
                # if we've now got everything, record successful run
                if qty + reserved_so_far == inv_req.quantity:
                    elapsed = completed_time - inv_req.timestamp
                    time_spent_serving += elapsed
                    requests_serviced += 1
                # otherwise we need to consider checking another bin
                else:
                    new_next_bin_to_check = (next_bin_to_check + 1) % rctr.num_bins()
                    # if we've checked every bin, give up
                    if new_next_bin_to_check == first_bin_checked:
                        # put everything back
                        requests_in_progress.append((
                            None,
                            reserved_so_far + qty,
                            None,
                            None,
                            completed_time
                        ))
                        requests_in_progress.sort(key=lambda x: x[4])
                        failed_requests += 1
                    else:
                        # we need to try another bin
                        requests_in_progress.append((
                            inv_req,
                            reserved_so_far + qty,
                            new_next_bin_to_check,
                            first_bin_checked,
                            completed_time
                        ))
                        requests_in_progress.sort(key=lambda x: x[4])
        # we should process the next item in the script
        else:
            item = script[0]
            del script[0]
            if isinstance(item, script_parser.InventoryRestock):
                rctr.add_stock(item.quantity, item.timestamp)
            elif isinstance(item, script_parser.InventoryRequest):
                completed_time, bin_id, qty = rctr.reserve_stock(
                    item.quantity,
                    item.timestamp
                )
                assert qty <= item.quantity
                if qty != item.quantity:
                    if rctr.num_bins() == 1:
                        # we're just out of inventory :(
                        requests_in_progress.append((
                            None,
                            qty,
                            None,
                            None,
                            completed_time
                        ))
                        requests_in_progress.sort(key=lambda x: x[4])
                        failed_requests += 1
                    else:
                        # need to enqueue trying another bin
                        requests_in_progress.append((
                            item,
                            qty,
                            (bin_id + 1) % rctr.num_bins(),
                            bin_id,
                            completed_time
                        ))
                        requests_in_progress.sort(key=lambda x: x[4])
                else:
                    elapsed = completed_time - item.timestamp
                    time_spent_serving += elapsed
                    requests_serviced += 1
    return time_spent_serving / requests_serviced, (requests_serviced) / (requests_serviced + failed_requests)

def handle_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", help="CSV filename to run")
    return parser.parse_args()

def main():
    args = handle_arguments()
    search_space = np.arange(1, 40, dtype=int)
    success_rates = np.zeros_like(search_space, dtype=float)
    avg_service_times = np.zeros_like(search_space, dtype=float)
    for index in range(len(search_space)):
        avg_service_time, success_rate = perform_experiment(int(search_space[index]), args.filename)
        success_rates[index] = success_rate
        avg_service_times[index] = avg_service_time
        print(index)
    plt.scatter(search_space, avg_service_times)
    plt.show()

main()
