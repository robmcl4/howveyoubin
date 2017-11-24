"""
adaptors.py

Contains all self-adaptive components for the system
"""


class PIAdaptor:
    
    def __init__(self):
        self.accumulated_error = 0

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
        err = measurement - set_point
        self.accumulated_error += err
        p = 5 * err
        i = 0.4 * self.accumulated_error
        return max(1, int(round(p + i)) + current_bins)
