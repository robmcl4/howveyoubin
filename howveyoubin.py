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
import history_recorder
import adaptors

# initial number of bins
INITIAL_BINS = 400


# seed
RAND_SEED = 1


# average service time, seconds
SERVICE_TIME = 0.15


# the number of time steps between invoking self-adaptive component
TIME_BETWEEN_ADAPTATION = 10


class ReturnInventoryRequest:
    """
    We've failed to get everything we need, just put everything back on the
    shelves. Represents the data needed to do that.
    """

    def __init__(self,
                 original_request: script_parser.InventoryRequest,
                 quantity: int,
                 queue_time: float,
                 service_time: float,
                 bins_checked: int,
                 timestamp: float):
        """
        Creates this ReturnInventoryRequest
        Args:
            original_request: the original InventoryRequest that's now failed
            quantity: the number of items to give back
            queue_time: the amount of time spent queueing
            service_time: the amount of time spent in bin service
            bins_checked: the number of bins this request had to check
            timestamp: when to put them back
        """
        self.original_request = original_request
        self.quantity = quantity
        self.queue_time = queue_time
        self.service_time = service_time
        self.bins_checked = bins_checked
        self.timestamp = timestamp


class RetryInventoryRequest:
    """
    Represents the intermediate state in attempting to reserve inventory.
    """

    def __init__(self,
                 original_request: script_parser.InventoryRequest,
                 reserved_so_far: int,
                 first_bin_checked: int,
                 queue_time_so_far: float,
                 service_time_so_far: float,
                 timestamp: float):
        """
        Creates this RetryInvenvoryRequest
        Args:
            original_request: the originating request
            reserved_so_far: the quantity of item which we've managed to reserve
            first_bin_checked: the first bin we checked
            queue_time_so_far: the amount of time spent in the queue
            service_time_so_far: the amount of time spent in service
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
        self.queue_time_so_far = queue_time_so_far
        self.service_time_so_far = service_time_so_far
        self.timestamp = timestamp
        self.bins_checked = 1


class AdaptNow:
    """
    Represents that we should call self-adaptive component at this time
    """

    def __init__(self, timestamp: float):
        """
        Constructs the adapt command
        Args:
            timestamp: float, when to adapt
        """
        self.timestamp = timestamp


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
    Returns a Recorder object
    """
    script_name = filename
    script = script_parser.parse_script(script_name)
    rctr = reactor.Reactor(0, num_bins, 0, SERVICE_TIME, RAND_SEED)
    script_start = script[0].timestamp
    script_end = script[-1].timestamp
    recorder = history_recorder.Recorder(TIME_BETWEEN_ADAPTATION, script_end)
    adaptor = adaptors.PIAdaptor()

    for ts in np.arange(script_start, script_end, TIME_BETWEEN_ADAPTATION):
        a = AdaptNow(ts)
        insert_action_sorted(script, a)

    recorder.record_num_bins(num_bins, 0)

    # iterate while there's still work to do, and 
    while len(script) > 0:
        curr_item = script[0]
        del script[0]

        if isinstance(curr_item, AdaptNow):
            # we adapt!
            new_bin_num = adaptor.adapt(
                rctr.num_bins(),
                recorder.get_avg_service_time_at(curr_item.timestamp),
                recorder.get_avg_queue_time_at(curr_item.timestamp),
                recorder.get_request_rate_at(curr_item.timestamp),
                rctr.stock_available(),
                recorder.get_bins_checked_at(curr_item.timestamp),
                rctr.avg_utilization(max(0, curr_item.timestamp - TIME_BETWEEN_ADAPTATION), curr_item.timestamp),
                curr_item.timestamp
            )
            rctr.reshape_num_bins(new_bin_num, curr_item.timestamp)
            recorder.record_num_bins(new_bin_num, curr_item.timestamp)
        if isinstance(curr_item, ReturnInventoryRequest):
            # we need to reshelve some inventory
            rctr.add_stock(curr_item.quantity, curr_item.timestamp)
            recorder.record_event(
                curr_item.queue_time,
                curr_item.service_time,
                rctr.stock_available(),
                curr_item.bins_checked,
                curr_item.timestamp
            )
        if isinstance(curr_item, script_parser.InventoryRestock):
            # natural restock
            rctr.add_stock(curr_item.quantity, curr_item.timestamp)
            recorder.record_restock(curr_item.timestamp)
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
                        curr_item.queue_time_so_far,
                        curr_item.service_time_so_far,
                        curr_item.bins_checked,
                        curr_item.timestamp
                    )
                )
            # we haven't tried all bins, so we should totally try to get more
            # inventory
            else:
                next_bin = (curr_item.first_bin_checked +
                            curr_item.bins_checked) % rctr.num_bins()
                queue_time, service_time, _, qty_reserved = rctr.reserve_stock(
                    curr_item.original_request.quantity - curr_item.reserved_so_far,
                    curr_item.timestamp,
                    service_bin_id=next_bin
                )
                curr_item.queue_time_so_far += queue_time
                curr_item.service_time_so_far += service_time
                completed_time = (curr_item.original_request.timestamp +
                                  curr_item.queue_time_so_far +
                                  curr_item.service_time_so_far)
                # if we've now got everything, record successful run
                if qty_reserved + curr_item.reserved_so_far == curr_item.original_request.quantity:
                    recorder.record_event(
                        curr_item.queue_time_so_far,
                        curr_item.service_time_so_far,
                        rctr.stock_available(),
                        curr_item.bins_checked + 1,
                        completed_time
                    )
                # otherwise we need to check another bin
                else:
                    curr_item.bins_checked += 1
                    curr_item.timestamp = completed_time
                    insert_action_sorted(script, curr_item)
        elif isinstance(curr_item, script_parser.InventoryRequest):
            recorder.record_start_request(curr_item.timestamp)
            queue_time, service_time, bin_id, qty = rctr.reserve_stock(
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
                        queue_time,
                        service_time,
                        curr_item.timestamp + queue_time + service_time
                    )
                )
            else:
                recorder.record_event(
                    queue_time,
                    service_time,
                    rctr.stock_available(),
                    1,
                    curr_item.timestamp + queue_time + service_time
                )
    return recorder


def handle_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", help="CSV filename to run")
    parser.add_argument("max_bins", type=int, help="max number of bins to search")
    parser.add_argument("-t",
        "--time-plot",
        help="plot a time-plot of performance with the given number of bins",
        action='store_true')
    return parser.parse_args()


def plot_range_of_bins(max_bins, fname):
    search_space = np.arange(1, max_bins, max(1, max_bins / 50), dtype=int)
    avg_queue_times = np.zeros_like(search_space, dtype=float)
    avg_service_times = np.zeros_like(search_space, dtype=float)
    for index in range(len(search_space)):
        recorder = perform_experiment(int(search_space[index]), fname)
        queue_times_avgs, service_times_avgs, _ = recorder.get_timelog()
        avg_queue_times[index] = np.average(queue_times_avgs)
        avg_service_times[index] = np.average(service_times_avgs)
        print(search_space[index])
    plt.title('Avg. Response Time vs Number of Bins')
    plt.xlabel('Number of Bins')
    plt.ylabel('Avg. Response Time')
    plt.bar(search_space, avg_queue_times, 1, label='avg. queue time')
    plt.bar(search_space, avg_service_times, 1, bottom=avg_queue_times, label='avg. service time')
    plt.legend()
    plt.show()


def plot_timeplot(num_bins, fname):
    assert num_bins > 0
    result = perform_experiment(num_bins, fname)
    queue_times_avgs, service_times_avgs, stock_avgs = result.get_timelog()
    x_axis_values = np.zeros_like(queue_times_avgs, dtype=float)
    for i in range(len(x_axis_values)):
        x_axis_values[i] = result.sample_rate * i
    fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, sharex=True)
    ax1.set_xlabel('Elapsed Time')
    ax1.set_ylabel('Resp. Time')
    ax1.plot(
        x_axis_values,
        queue_times_avgs,
        label='queue time'
    )
    ax1.plot(
        x_axis_values,
        service_times_avgs,
        label='service time'
    )
    for restock in result.get_restocks():
        ax1.axvline(x=restock, linestyle='-.', color='c')
    ax1.legend(loc=0)
    ax1.set_ylim(ymin=0)

    ax2.plot(
        x_axis_values,
        np.resize(result.num_started_requests, len(x_axis_values)) / result.sample_rate,
        'g:',
        label='requests/s'
    )
    ax2.set_ylabel('requests/s')
    ax2.legend(loc=0)
    ax2.set_ylim(ymin=0)

    ax3.plot(
        x_axis_values,
        stock_avgs,
        'r--',
        label='supply'
    )
    ax3.legend(loc=0)
    ax3.set_ylabel('items')
    ax3.set_ylim(ymin=0)

    ax4.plot(
        np.resize(result.bin_nums_timestamps, result.bin_nums_next_index),
        np.resize(result.bin_nums, result.bin_nums_next_index),
        label='number of bins'
    )
    ax4.legend(loc=0)
    ax4.set_ylabel('bins')
    ax4.set_ylim(ymin=0)

    plt.show()


def main():
    args = handle_arguments()
    if args.time_plot:
        plot_timeplot(args.max_bins, args.filename)
    else:
        plot_range_of_bins(args.max_bins, args.filename)


main()
