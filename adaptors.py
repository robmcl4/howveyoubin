"""
adaptors.py

Contains all self-adaptive components for the system
"""

import itertools

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

class RLAdaptor:
    HIGH = 1
    MEDIUM = 2
    LOW = 3
    NONE = 4

    ADD_TEN = 0
    ADD_ONE = 1
    ADD_NONE = 2
    REM_ONE = 3
    REM_TEN = 4

    STATES = list(itertools.product([
        [HIGH, MEDIUM, LOW], # arrival rate
        [HIGH, MEDIUM, LOW], # service time
        [HIGH, MEDIUM, LOW], # queue time
        [HIGH, MEDIUM, LOW, NONE] # stock
    ]))

    ARRIVAL_THRESHOLDS = (2, 10) # lower bounds medium and high, respectively
    SERVICE_TIME_THRESHOLDS = (0.05, 0.25) # lower bounds on medium and high, respectively
    QUEUE_TIME_THRESHOLDS = (0.05, 0.5) # lower bounds on medium and high, respectively
    STOCK_THRESHOLDS = (500, 10000) # lower bounds on medium and high, respectively

    ACTIONS = [
        ADD_TEN, ADD_ONE, ADD_NONE, REM_ONE, REM_TEN
    ]

    def discretize_state(self, arrival_rate, service_time, queue_time, stock):
        a = RLAdaptor.LOW
        if arrival_rate > RLAdaptor.ARRIVAL_THRESHOLDS[0]:
            a = RLAdaptor.MEDIUM
        if arrival_rate > RLAdaptor.ARRIVAL_THRESHOLDS[1]:
            a = RLAdaptor.HIGH
        st = RLAdaptor.LOW
        if service_time > RLAdaptor.SERVICE_TIME_THRESHOLDS[0]:
            st = RLAdaptor.MEDIUM
        if service_time > RLAdaptor.SERVICE_TIME_THRESHOLDS[1]:
            st = RLAdaptor.HIGH
        qt = RLAdaptor.LOW
        if queue_time > RLAdaptor.QUEUE_TIME_THRESHOLDS[0]:
            st = RLAdaptor.MEDIUM
        if queue_time > RLAdaptor.QUEUE_TIME_THRESHOLDS[1]:
            st = RLAdaptor.HIGH
        s = RLAdaptor.NONE
        if stock > 0:
            s = RLAdaptor.LOW
        if stock > RLAdaptor.STOCK_THRESHOLDS[0]:
            s = RLAdaptor.MEDIUM
        if stock > RLAdaptor.STOCK_THRESHOLDS[1]:
            s = RLAdaptor.HIGH
        state_id = RLAdaptor.STATES.index((a,st,qt,s))
        assert state_id >= 0
        return state_id

    def __init__(self):
        from tensorforce.agents import PPOAgent
        import os
        self.agent = PPOAgent(
            states_spec=dict(type='float', shape=(5,)),
            actions_spec=dict(type='int', num_actions=len(RLAdaptor.ACTIONS)),
            network_spec=[
                dict(type='dense', size=64),
                dict(type='dense', size=32),
                dict(type='dense', size=16)
            ],
            batch_size=1000,
            step_optimizer=dict(
                type='adam',
                learning_rate=1e-4
            )
        )
        if os.path.isdir('models'):
            self.agent.restore_model('models/')
        self.last_resp_time = None

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
        current_resp_time = current_service_time + current_queue_time
        # state = self.discretize_state(current_request_rate, current_service_time, current_queue_time, current_stock)
        if self.last_resp_time is not None:
            # calculate reward
            if current_resp_time > 0:
                perc_change = (current_resp_time - self.last_resp_time) / current_resp_time
                self.agent.observe(reward=-perc_change, terminal=False)
        self.last_resp_time = current_resp_time
        action = self.agent.act((current_bins, current_request_rate, current_service_time, current_queue_time, current_stock))

        if action == RLAdaptor.ADD_TEN:
            return current_bins + 10
        elif action == RLAdaptor.ADD_ONE:
            return current_bins + 1
        elif action == RLAdaptor.ADD_NONE:
            return current_bins
        elif action == RLAdaptor.REM_ONE:
            return max(1, current_bins - 1)
        elif action == RLAdaptor.REM_TEN:
            return max(1, current_bins - 10)
        raise Exception('this should never happen')

    def save(self):
        self.agent.save_model('models/')
