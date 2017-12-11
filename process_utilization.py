import csv
import numpy as np
import matplotlib.pyplot as plt


FNAME = 'utilization.csv'


def min_resp_time_for_arrival_rate(arrival_rates, resp_times, arrival_rate):
    # minimize response time for the target arrival rate
    ret = float('inf')
    for arrival_rate_, resp_time in zip(arrival_rates, resp_times):
        if arrival_rate_ == arrival_rate:
            ret = min(ret, resp_time)
    return ret


def resp_time_of_closest_utilization(arrival_rates, resp_times, utilizations, arrival_rate, utilization):
    # approximate the response time for a given utilization setpoint and a given arrival rate
    closest_utilization = float('2') # arrival rates are 0-1, this is 'absurd' value
    closest_resp_time = -1
    for arrival_rate_, resp_time, utilization_ in zip(arrival_rates, resp_times, utilizations):
        if arrival_rate_ == arrival_rate:
            if abs(utilization_ - utilization) < abs(closest_utilization - utilization):
                closest_utilization = utilization_
                closest_resp_time = resp_time
    return resp_time


def optimal_utilization(arrival_rates, resp_times, utilizations):
    unique_arrival_rates = set(arrival_rates)
    best_err = float('inf')
    best_utilization = -1
    for exploring_utilization in np.linspace(0.0025, 0.1, 100):
        err = 0
        for arrival_rate in unique_arrival_rates:
            optimal_resp_time = min_resp_time_for_arrival_rate(arrival_rates, resp_times, arrival_rate)
            resp_time = resp_time_of_closest_utilization(arrival_rates, resp_times, utilizations, arrival_rate, exploring_utilization)
            err += resp_time - optimal_resp_time
        if err < best_err:
            best_err = err
            best_utilization = exploring_utilization
    return best_utilization

def main():
    arrival_rates = np.loadtxt(FNAME, dtype=float, skiprows=1, usecols=(0,), delimiter=',')
    bins = np.loadtxt(FNAME, dtype=np.uint8, skiprows=1, usecols=(1,), delimiter=',')
    utilizations = np.loadtxt(FNAME, dtype=float, skiprows=1, usecols=(2,), delimiter=',')
    resp_times = np.loadtxt(FNAME, dtype=float, skiprows=1, usecols=(3,), delimiter=',')
    best_utilization = optimal_utilization(arrival_rates, resp_times, utilizations)
    print('best utilization:', best_utilization)
    plt.scatter(utilizations, resp_times, s=1.8, c=bins*2, cmap='plasma')
    plt.axvline(best_utilization, color='cyan')
    plt.xlabel('utilization')
    plt.ylabel('response time')
    plt.show()


main()
