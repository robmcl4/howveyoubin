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
        # same as above, except for number of bins checked before completion
        self.checked_numerator = np.zeros(1024, dtype=np.uint64)
        # the number of records seen in each sample bin
        self.num_records = np.zeros(1024, dtype=np.uint64)
        # the complete list of timestamps when we did restocks
        self.restocks = np.zeros(1024, dtype=float)
        self.num_restocks = 0
        # the number of /incoming/ (not completed) requests in each time-bin
        self.num_started_requests = np.zeros(1024, dtype=np.uint64)
        self.oldest_started_request_timestamp = 0
        # the number of bins (as two parallel arrays)
        self.bin_nums = np.zeros(1024, dtype=np.uint16)
        self.bin_nums_timestamps = np.zeros(1024, dtype=float)
        self.bin_nums_next_index = 0
        self.script_end = script_end

    def record_num_bins(self, num_bins: int, timestamp: float):
        """
        Record how many bins we're using at a given timestamp
        Args:
            num_bins: int, the number of bins in use
            timestamp: float, what time this quantity of bins are in use
        """
        assert timestamp >= 0
        assert num_bins > 0
        if self.bin_nums_next_index >= len(self.bin_nums):
            new_size = len(self.bin_nums) * 2
            assert new_size <= 32768
            self.bin_nums.resize(new_size)
            self.bin_nums_timestamps.resize(new_size)
        self.bin_nums[self.bin_nums_next_index] = num_bins
        self.bin_nums_timestamps[self.bin_nums_next_index] = timestamp
        self.bin_nums_next_index += 1

    def record_start_request(self, timestamp: float):
        """
        Record that a request has begun
        Args:
            timestamp: the time when this request begins
        """
        assert timestamp > 0
        self.oldest_started_request_timestamp = max(self.oldest_started_request_timestamp, timestamp)
        bin_index = math.floor(timestamp / self.sample_rate)
        if len(self.num_started_requests) <= bin_index:
            new_size = len(self.num_started_requests) * 2
            assert new_size <= 32768
            self.num_started_requests.resize(new_size)
        self.num_started_requests[bin_index] += 1

    def record_event(self, queue_time: float, service_time: float, stock_left: int, bins_checked: int, timestamp: float):
        """
        Record that an event happened with the given queue and service time
        Args:
            queue_time - float, time spent queueing
            service_time - float, time spent in the service worker (bin)
            stock_left - int, the number of items left in stock after this request
            bins_checked - int, the number of bins this request had to check before it completed
            timestamp - float, the timestamp when this succeeded
        """
        if timestamp > self.script_end:
            return
        assert timestamp >= 0
        assert bins_checked > 0
        self.oldest_timestamp = max(self.oldest_timestamp, timestamp)
        bin_index = math.floor(timestamp / self.sample_rate)
        # if we need to grow, do that
        if len(self.num_records) <= bin_index:
            new_size = len(self.num_records) * 2
            assert new_size <= 32768
            self.queue_waiting_numerator.resize(new_size)
            self.service_time_numerator.resize(new_size)
            self.stock_numerator.resize(new_size)
            self.checked_numerator.resize(new_size)
            self.num_records.resize(new_size)
        self.queue_waiting_numerator[bin_index] += queue_time
        self.service_time_numerator[bin_index] += service_time
        self.stock_numerator[bin_index] += stock_left
        self.checked_numerator[bin_index] += bins_checked
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

        return (
            np.divide(np.resize(self.queue_waiting_numerator, num_bins),
                      np.resize(self.num_records + mask, num_bins)),
            np.divide(np.resize(self.service_time_numerator, num_bins),
                      np.resize(self.num_records + mask, num_bins)),
            np.divide(np.resize(self.stock_numerator, num_bins),
                      np.resize(self.num_records + mask, num_bins))
        )

    def get_avg_service_time_at(self, timestamp: float) -> float:
        """
        Gets the average time spent in service at the given timestamp
        Args:
            timestamp: when to check
        Retutrns:
            the avg service time
        """
        bin_index = math.floor(timestamp / self.sample_rate)
        # if timestamp is super-duper close (or exactly) a new epoch,
        # report the last epoch
        if 0 <= ((timestamp % self.sample_rate) / self.sample_rate) <= 0.05:
            bin_index = max(0, bin_index-1)
        num = self.service_time_numerator[bin_index]
        denom = self.num_records[bin_index]
        if denom == 0:
            return 0
        return num / denom

    def get_avg_queue_time_at(self, timestamp: float) -> float:
        """
        Gets the average time spent in queue at the given timestamp
        Args:
            timestamp: when to check
        Retutrns:
            the avg queue time
        """
        bin_index = math.floor(timestamp / self.sample_rate)
        # if timestamp is super-duper close (or exactly) a new epoch,
        # report the last epoch
        if 0 <= ((timestamp % self.sample_rate) / self.sample_rate) <= 0.05:
            bin_index = max(0, bin_index-1)
        num = self.queue_waiting_numerator[bin_index]
        denom = self.num_records[bin_index]
        if denom == 0:
            return 0
        return num / denom

    def get_avg_stock_at(self, timestamp: float) -> float:
        """
        Gets the average stock in this timestamp's windowed bin
        Args:
            timestamp: when to check
        Retutrns:
            the average stock
        """
        bin_index = math.floor(timestamp / self.sample_rate)
        # if timestamp is super-duper close (or exactly) a new epoch,
        # report the last epoch
        if 0 <= ((timestamp % self.sample_rate) / self.sample_rate) <= 0.05:
            bin_index = max(0, bin_index-1)
        num = self.stock_numerator[bin_index]
        denom = self.num_records[bin_index]
        if denom == 0:
            return 0
        return num / denom

    def get_request_rate_at(self, timestamp: float) -> float:
        """
        Gets the requests / time unit at this timestamp's windowed bin
        Args:
            timestamp: when to check
        Returns:
            the average request rate
        """
        bin_index = math.floor(timestamp / self.sample_rate)
        # if this bin isn't full yet we need to adjust for that
        if self.oldest_started_request_timestamp < self.sample_rate * (bin_index + 1):
            bin_time_elapsed = self.oldest_started_request_timestamp % self.sample_rate
            prev_rate = 0
            if bin_index > 0:
                prev_rate = self.num_started_requests[bin_index-1] / self.sample_rate
            curr_rate = prev_rate
            if bin_time_elapsed != 0 and len(self.num_started_requests) > bin_index:
                curr_rate = self.num_started_requests[bin_index] / bin_time_elapsed
            return curr_rate * 0.7 + prev_rate * 0.3
        return self.num_started_requests[bin_index] / self.sample_rate

    def get_bins_checked_at(self, timestamp: float) -> float:
        """
        Gets the average number of bins checked before a request completes
        Args:
            timestamp: when to check
        Returns:
            the average number of bins checked
        """
        bin_index = math.floor(timestamp / self.sample_rate)
        # if timestamp is super-duper close (or exactly) a new epoch,
        # report the last epoch
        if 0 <= ((timestamp % self.sample_rate) / self.sample_rate) <= 0.05:
            bin_index = max(0, bin_index-1)
        num = self.checked_numerator[bin_index]
        denom = self.num_records[bin_index]
        if denom == 0:
            return 0
        return num / denom
