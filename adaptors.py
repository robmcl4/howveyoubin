"""
adaptors.py

Contains all self-adaptive components for the system
"""

class DummyAdaptor:
    
    def adapt(
            self,
            current_bins: int,
            current_service_time: float,
            current_queue_time: float,
            current_request_rate: float,
            current_stock: int,
            timestamp: float
        ) -> int:
        if timestamp > 300:
            return 40
        return 1
