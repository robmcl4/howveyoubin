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
SERVICE_TIME = 0.15


class ReturnInventoryRequest:
    """
    We've failed to get everything we need, just put everything back on the
    shelves. Represents the data needed to do that.
    """

    def __init__(self,
                 original_request: script_parser.InventoryRequest,
                 quantity: int,
                 timestamp: float):
        """
        Creates this ReturnInventoryRequest
        Args:
            original_request: the original InventoryRequest that's now failed
            quantity: the number of items to give back
            timestamp: when to put them back
        """
        self.original_request = original_request
        self.quantity = quantity
        self.timestamp = timestamp


class RetryInventoryRequest:
    """
    Represents the intermediate state in attempting to reserve inventory.
    """

    def __init__(self,
                 original_request: script_parser.InventoryRequest,
                 reserved_so_far: int,
                 first_bin_checked: int,
                 timestamp: float):
        """
        Creates this RetryInvenvoryRequest
        Args:
            original_request: the originating request
            reserved_so_far: the quantity of item which we've managed to reserve
            first_bin_checked: the first bin we checked
            timestamp: float, when to execute this request
        """
        assert isinstance(original_request, script_parser.InventoryRequest)
        assert reserved_so_far >= 0
        assert reserved_so_far < original_request.quantity
        assert first_bin_checked >= 0
        assert timestamp >= 0
        self.original_request = original_request
        self.reserved_so_far = reserved_so_far
        self.first_bin_checked = first_bin_checked
        self.timestamp = timestamp
        self.bins_checked = 1


def insert_action_sorted(lst, action):
    """
    Inserts the given action in-place into the given list
    """
    insert_index = 0
    while (insert_index < len(lst) and
           action.timestamp > lst[insert_index].timestamp):
        insert_index += 1
    lst.insert(insert_index, action)
    assert insert_index == 0 or lst[insert_index-1].timestamp <= lst[insert_index].timestamp
    assert insert_index == len(lst)-1 or lst[insert_index].timestamp <= lst[insert_index+1].timestamp


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

    # iterate while there's still work to do
    while len(script) > 0:
        curr_item = script[0]
        del script[0]

        if (isinstance(curr_item, ReturnInventoryRequest) or
            isinstance(curr_item, script_parser.InventoryRestock)):
            # we need to reshelve some inventory
            rctr.add_stock(curr_item.quantity, curr_item.timestamp)
        if isinstance(curr_item, RetryInventoryRequest):
            assert curr_item.original_request.quantity > curr_item.reserved_so_far
            # we should continue a request
            # ... but if we've tried all the bins, give up
            if curr_item.bins_checked >= rctr.num_bins():
                insert_action_sorted(
                    script,
                    ReturnInventoryRequest(
                        curr_item.original_request,
                        curr_item.reserved_so_far,
                        curr_item.timestamp
                    )
                )
            # we haven't tried all bins, so we should totally try to get more
            # inventory
            else:
                next_bin = (curr_item.first_bin_checked +
                            curr_item.bins_checked) % rctr.num_bins()
                completed_time, service_bin, qty_reserved = rctr.reserve_stock(
                    curr_item.original_request.quantity - curr_item.reserved_so_far,
                    curr_item.timestamp,
                    service_bin_id=next_bin
                )
                # if we've now got everything, record successful run
                if qty_reserved + curr_item.reserved_so_far == curr_item.original_request.quantity:
                    elapsed = completed_time - curr_item.original_request.timestamp
                    assert elapsed > 0
                    time_spent_serving += elapsed
                    requests_serviced += 1
                # otherwise we need to check another bin
                else:
                    curr_item.bins_checked += 1
                    curr_item.timestamp = completed_time
                    insert_action_sorted(script, curr_item)
        elif isinstance(curr_item, script_parser.InventoryRequest):
            completed_time, bin_id, qty = rctr.reserve_stock(
                curr_item.quantity,
                curr_item.timestamp
            )
            assert qty <= curr_item.quantity
            if qty != curr_item.quantity:
                insert_action_sorted(
                    script,
                    RetryInventoryRequest(
                        curr_item,
                        qty,
                        bin_id,
                        completed_time
                    )
                )
            else:
                elapsed = completed_time - curr_item.timestamp
                assert elapsed > 0
                time_spent_serving += elapsed
                requests_serviced += 1
    return time_spent_serving / requests_serviced, (requests_serviced) / (requests_serviced + failed_requests)


def handle_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", help="CSV filename to run")
    parser.add_argument("max_bins", type=int, help="max number of bins to search")
    return parser.parse_args()


def main():
    args = handle_arguments()
    search_space = np.arange(1, args.max_bins, max(1, args.max_bins / 50), dtype=int)
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
