"""
history_recorder.py

feeds and remembers historical performance metrics of the management system
"""

import math
import numpy as np


class Recorder:    
    def __init__(self, sample_rate: float, script_end: float):
        """
        Creates a recorder
        Args:
            sample_rate - float, the width of a sampling bin in terms of timestamps
            script_end - float, when the experiment ends (when to stop recording events)
        """
        assert sample_rate > 0
        self.sample_rate = sample_rate
        self.oldest_timestamp = 0
        # when calculating the average, this is the numerator of time spent
        # waiting in a queue
        self.queue_waiting_numerator = np.zeros(1024, dtype=float)
        # same as above, except for time spent servicing (in-bin)
        self.service_time_numerator = np.zeros(1024, dtype=float)
        # same as above, except for current inventory stock
        self.stock_numerator = np.zeros(1024, dtype=np.uint64)
        # the number of records seen in each sample bin
        self.num_records = np.zeros(1024, dtype=np.uint64)
        self.restocks = np.zeros(1024, dtype=float)
        self.num_restocks = 0
        self.script_end = script_end

    def record_event(self, queue_time: float, service_time: float, stock_left: int, timestamp: float):
        """
        Record that an event happened with the given queue and service time
        Args:
            queue_time - float, time spent queueing
            service_time - float, time spent in the service worker (bin)
            stock_left - int, the number of items left in stock after this request
            timestamp - float, the timestamp when this succeeded
        """
        if timestamp > self.script_end:
            return
        assert timestamp >= 0
        self.oldest_timestamp = max(self.oldest_timestamp, timestamp)
        bin_index = math.floor(timestamp / self.sample_rate)
        # if we need to grow, do that
        if len(self.num_records) < bin_index:
            new_size = len(self.num_records) * 2
            assert new_size <= 32768
            self.queue_waiting_numerator.resize(new_size)
            self.service_time_numerator.resize(new_size)
            self.stock_numerator.resize(new_size)
            self.num_records.resize(new_size)
        self.queue_waiting_numerator[bin_index] += queue_time
        self.service_time_numerator[bin_index] += service_time
        self.stock_numerator[bin_index] += stock_left
        self.num_records[bin_index] += 1

    def record_restock(self, timestamp: float):
        """
        Records that a restock happened at the given timestamp
        Args:
            timestamp: when the restock occurred
        """
        if timestamp > self.script_end:
            return
        assert timestamp >= 0
        self.num_restocks += 1
        if self.num_restocks >= len(self.restocks):
            new_size = len(self.restocks) * 2
            assert new_size <= 32768
            self.restocks.resize(new_size)
        self.restocks[self.num_restocks-1] = timestamp

    def get_restocks(self):
        """
        Gets a numpy-array of floats indicating timestamps of restocks
        Returns:
            nx1 array of floats
        """
        return np.resize(self.restocks, self.num_restocks)

    def get_timelog(self):
        """
        Gets a numpy-summary of the performance metrics over the recording
        time-window.
        returns
            (
                queue_time_average,
                service_time_average,
                stock_average
            ) for each bin-window (bins have `self.sample_rate` width, in time units)
        """
        num_bins = math.floor(self.oldest_timestamp / self.sample_rate) + 1
        # make all zeros in the denominator into 1s
        # (doesn't matter, numerator is 0 anyway)
        mask = np.zeros_like(self.num_records)
        for index, val in enumerate(self.num_records):
            if val == 0:
                mask[index] = 1

        last_bin = math.floor(self.oldest_timestamp / self.sample_rate)

        return (
            np.divide(np.resize(self.queue_waiting_numerator, num_bins),
                      np.resize(self.num_records + mask, num_bins)),
            np.divide(np.resize(self.service_time_numerator, num_bins),
                      np.resize(self.num_records + mask, num_bins)),
            np.divide(np.resize(self.stock_numerator, num_bins),
                      np.resize(self.num_records + mask, num_bins))
        )
