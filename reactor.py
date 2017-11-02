"""
reactor.py

manages instantaneous state history throughout time as
a transactional record
"""

import random
import math


class Reactor:

    def __init__(self, stock, bins, created_at, service_time, seed):
        """
        Intitializes this inventory-processor
        params:
            stock - int, initial supply of goods
            bins - int, initial number of bins
            created_at - float, what timestamp this bin was created
            service_time - float, average time it takes to reserve stock, based
                on an exponential distribution
            seed - seed for the random number generator
        """
        self.rand = random.Random()
        self.rand.seed(seed)
        self.bins = []

        # assign stock to bins as uniformly as possible (the last bin may
        # have a few less than the others)
        stock_per_bin = math.ceil(stock / bins)
        stock_assigned = 0
        for _ in range(bins):
            stock_to_assign = min(stock_per_bin, stock - stock_assigned)
            stock_assigned += stock_to_assign
            self.bins.append(
                Bin(
                    stock_to_assign,
                    created_at,
                    service_time,
                    self.rand.randint(0, 10000)
                )
            )
        self._last_time_used = created_at

    def num_bins(self):
        """
        returns the number of bins this reactor has
        """
        return len(self.bins)

    def reserve_stock(self, quantity, timestamp, service_bin_id=None):
        """
        Uses the pool of bins to reserve inventory stock
        params:
            quantity - int, the number of items to reserve
            timestamp - when this request executes
            service_bin_id - optional, int, ID of the bin to request from
        returns:
            (completed_time, service_bin_id, quantity_reserved)
        """
        assert timestamp >= self._last_time_used
        self._last_time_used = timestamp

        # pick a random bin
        if service_bin_id is None:
            service_bin_id = self.rand.randrange(0, len(self.bins))
        bin_ = self.bins[service_bin_id]
        completed_time, quantity_reserved = bin_.reserve_stock(
            quantity,
            timestamp
        )
        return completed_time, service_bin_id, quantity_reserved

    def add_stock(self, quantity, timestamp, service_bin_ids=None):
        """
        Adds more inventory stock to the pool of bins
        params:
            quantity - int, number of items to add
            timestamp - when this request executes
            service_bin_ids - optional, [int], IDs of the bins to add to
        returns:
            [service_bin_id] - the bins which were modified
        """
        assert timestamp >= self._last_time_used
        self._last_time_used = timestamp
        
        # strategy: immediately gets in line for all identified bins
        # and evenly distributes all inventory between them
        if service_bin_ids is None:
            service_bin_ids = list(range(len(self.bins)))
        # assign to bins in random order
        self.rand.shuffle(service_bin_ids)
        stock_per_bin = math.ceil(quantity / len(self.bins))
        stock_assigned = 0

        for bin_id in service_bin_ids:
            stock_to_assign = min(stock_per_bin, quantity - stock_assigned)
            stock_assigned += stock_to_assign
            self.bins[bin_id].add_stock(stock_to_assign, timestamp)
        return sorted(service_bin_ids)


class Bin:

    def __init__(self, stock, created_at, service_time, seed):
        """
        Initialize this bin
        params:
            stock - int, the quantity of resource this stock holds
            created_at - float, what timestamp this bin was created
            service_time - float, average time it takes to reserve stock, based
                on an exponential distribution
            seed - int, random num gen seed
        """
        # 
        # Contains the list of times during which this bin is locked, for
        # later lookup. Stored as (start, end) tuples, indicating end-exclusive
        # lock times
        self.locked_times = [(created_at, created_at)]
        #
        # Contains the history of this bin's item-stock as (time, quantity)
        # pairs
        self.stock = [(created_at, stock)]
        self.service_time = service_time
        self.rand = random.Random()
        self.rand.seed(seed)


    def reserve_stock(self, quantity, timestamp):
        """
        Attempts to reserve stock from this bin.
        params:
            quantity - the amount of stock needed
            timestamp - the current timestamp at the start of request
        returns:
            (end_timestamp, quantity) indicating when the request completed
            and how much was reserved
        """
        # wait for the lock to be released
        end_of_queue_time = self._wait_in_queue(timestamp)
        # find out how long we're randomly spending in processing
        service_time = self.rand.expovariate(1 / float(self.service_time))
        # record how long we've now locked the bin
        self.locked_times.append(
            (end_of_queue_time, end_of_queue_time + service_time)
        )
        # take as much supply as we can
        true_remaining_stock_at_service = self._remaining_stock_at_time(
            end_of_queue_time
        )
        stock_left = max(0, true_remaining_stock_at_service - quantity)
        self.stock.append(
            (end_of_queue_time + service_time, stock_left)
        )
        return (
            end_of_queue_time + service_time,
            true_remaining_stock_at_service - stock_left
        )

    def add_stock(self, quantity, timestamp):
        """
        Adds more inventory stock to the pool of bins
        params:
            quantity - int, number of items to add
            timestamp - when this request executes
        """
        # wait for the lock to be released
        end_of_queue_time = self._wait_in_queue(timestamp)
        # find out how long we're randomly spending in processing
        service_time = self.rand.expovariate(1 / float(self.service_time))
        # record how long we've now locked the bin
        self.locked_times.append(
            (end_of_queue_time, end_of_queue_time + service_time)
        )
        remaining_stock = self._remaining_stock_at_time(end_of_queue_time)
        self.stock.append(
            (end_of_queue_time + service_time, remaining_stock + quantity)
        )

    def _wait_in_queue(self, timestamp):
        """
        Gets the next available timestamp for when the bin is unlocked
        Returns:
            float, the timestamp for when next unlocked
        """
        return max(self.locked_times[-1][1], timestamp)
    
    def _remaining_stock_at_time(self, timestamp):
        """
        Gets the quantity of stock remaining at the given timestamp
        Returns:
            int, the stock remaining
        """
        return self.stock[-1][1]
