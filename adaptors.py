"""
adaptors.py

Contains all self-adaptive components for the system
"""


class PIDAdaptor:

    def __init__(self, kp, ki, kd, i_min, i_max):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.accumulated_error = 0
        self.previous_error = 0
        self.previous_time = 0
        self.i_max = i_max
        self.i_min = i_min

    def adapt(
            self,
            current_bins: int,
            current_service_time: float,
            current_queue_time: float,
            current_request_rate: float,
            current_stock: int,
            current_bins_checked: float,
            current_utilization: float,
            timestamp: float
        ) -> int:
        set_point = 0.1
        measurement = current_utilization
        err = set_point - measurement
        self.accumulated_error += err
        de = err - self.previous_error
        dt = timestamp - self.previous_time

        p = err
        i = self.accumulated_error
        if i > self.i_max:
            i = self.i_max
        elif i < self.i_min:
            i = self.i_min

        d = de/dt if dt != 0 else 1

        bin_delta = int(round(self.kp * p + self.ki * i + self.kd * d))

        self.previous_error = err
        self.previous_time = timestamp

        return max(1, bin_delta + current_bins)
