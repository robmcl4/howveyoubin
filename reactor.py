"""
reactor.py

manages instantaneous state history throughout time as
a transactional record
"""

import random
import math
from typing import List
from typing import Tuple


class Reactor:
    def __init__(self, stock: int, bins: int, created_at: float, service_time: float, seed: int):
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
        self.service_time = service_time

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

    def num_bins(self) -> int:
        """
        returns the number of bins this reactor has
        """
        return len(self.bins)

    def reserve_stock(self, quantity: int, timestamp: float, service_bin_id: int=None) -> Tuple[float, int, int]:
        """
        Uses the pool of bins to reserve inventory stock
        params:
            quantity - int, the number of items to reserve
            timestamp - when this request executes
            service_bin_id - optional, int, ID of the bin to request from
        returns:
            (queue_time, service_time, service_bin_id, quantity_reserved)
        """
        assert timestamp >= self._last_time_used
        self._last_time_used = timestamp

        # pick a random bin
        if service_bin_id is None:
            service_bin_id = self.rand.randrange(0, len(self.bins))
        bin_ = self.bins[service_bin_id]
        queue_time, service_time, quantity_reserved = bin_.reserve_stock(
            quantity,
            timestamp
        )
        return queue_time, service_time, service_bin_id, quantity_reserved

    def add_stock(self, quantity: int, timestamp: float, service_bin_ids:List[int] = None) -> List[int]:
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

    def reshape_num_bins(self, num_bins: int, timestamp: float) -> float:
        """
        Adjusts the number of bins up or down at the given timestamp
        Args:
            num_bins - int, the new number of bins to use
            timestamp - float, at what timestamp this adjustment begins
        Returns:
            time_completed
        """
        assert timestamp >= self._last_time_used
        self._last_time_used = timestamp

        if len(self.bins) == num_bins:
            # no work to do
            return timestamp
        
        # find out what the soonest time is that we can destroy the existing bins
        soonest_time = timestamp
        for bin_ in self.bins:
            available_after = bin_.next_unlocked(timestamp)
            if available_after > soonest_time:
                soonest_time = available_after
        
        stock = self.stock_available()
        del self.bins[:]

        # create new bins
        stock_per_bin = math.ceil(stock / num_bins)
        stock_assigned = 0
        for _ in range(num_bins):
            stock_to_assign = min(stock_per_bin, stock - stock_assigned)
            stock_assigned += stock_to_assign
            self.bins.append(
                Bin(
                    stock_to_assign,
                    soonest_time,
                    self.service_time,
                    self.rand.randint(0, 10000)
                )
            )
        
        # estimate how long it took us to make these new bins, and reserve them
        # all for that time
        service_time = self.rand.expovariate(1 / float(self.service_time))
        for bin_ in self.bins:
            bin_.locked_times.append((soonest_time, soonest_time + service_time))
        return soonest_time + service_time


    def stock_available(self) -> int:
        """
        Finds the quantity of items available
        Returns:
            int, the quantity of items available
        """
        ret = 0
        for bin_ in self.bins:
            ret += bin_.remaining_stock()
        return ret
    
    def avg_utilization(self, since: float, to: float) -> float:
        """
        Gets the average bin utilization as a percent of time
        Returns:
            float, from 0 to 1, percent of time spent utilized
        """
        s = sum(x.utilization_percent(since, to) for x in self.bins)
        return s / len(self.bins)

class Bin:
    def __init__(self, stock: int, created_at: float, service_time: float, seed: int):
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

    def reserve_stock(self, quantity: int, timestamp: float) -> Tuple[float, int]:
        """
        Attempts to reserve stock from this bin.
        params:
            quantity - the amount of stock needed
            timestamp - the current timestamp at the start of request
        returns:
            (queue_time, service_time, quantity)
                indicating how much time was spent in the queue, how much
                was spent in service, and the quantity reserved
        """
        # wait for the lock to be released
        end_of_queue_time = self.next_unlocked(timestamp)
        # find out how long we're randomly spending in processing
        service_time = self.rand.expovariate(1 / float(self.service_time))
        # record how long we've now locked the bin
        self.locked_times.append(
            (end_of_queue_time, end_of_queue_time + service_time)
        )
        # take as much supply as we can
        true_remaining_stock_at_service = self.remaining_stock()
        stock_left = max(0, true_remaining_stock_at_service - quantity)
        self.stock.append(
            (end_of_queue_time + service_time, stock_left)
        )
        return (
            end_of_queue_time - timestamp,
            service_time,
            true_remaining_stock_at_service - stock_left
        )

    def add_stock(self, quantity: int, timestamp: float):
        """
        Adds more inventory stock to the pool of bins
        params:
            quantity - int, number of items to add
            timestamp - when this request executes
        """
        # wait for the lock to be released
        end_of_queue_time = self.next_unlocked(timestamp)
        # find out how long we're randomly spending in processing
        service_time = self.rand.expovariate(1 / float(self.service_time))
        # record how long we've now locked the bin
        self.locked_times.append(
            (end_of_queue_time, end_of_queue_time + service_time)
        )
        remaining_stock = self.remaining_stock()
        self.stock.append(
            (end_of_queue_time + service_time, remaining_stock + quantity)
        )

    def next_unlocked(self, timestamp: float) -> float:
        """
        Gets the next available timestamp for when the bin is unlocked
        Args:
            timestamp: float, the timestamp to begin searching
        Returns:
            float, the timestamp for when next unlocked
        """
        return max(self.locked_times[-1][1], timestamp)

    def remaining_stock(self) -> int:
        """
        Gets the most recent quantity of stock remaining
        Returns:
            int, the stock remaining
        """
        return self.stock[-1][1]

    def utilization_percent(self, since: float, to: float) -> int:
        """
        Gets the utilization percent of this bin, as a percent of time
        spent busy over the given interval.
        Returns:
            float, from 0 to 1, indicating percent of time being utilized
        """
        if to == since:
            return 1
        since = max(since, self.locked_times[0][0])
        cumulative_time_locked = 0
        for start_lock, end_lock in self.locked_times:
            if start_lock >= to:
                continue
            if end_lock < since:
                continue
            start_lock = max(since, start_lock)
            end_lock = min(to, end_lock)
            cumulative_time_locked += end_lock - start_lock
        return cumulative_time_locked / (to - since)
