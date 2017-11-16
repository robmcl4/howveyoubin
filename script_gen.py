#!/usr/bin/python3
"""
Generates runtime script
"""

import argparse
import csv
import random
import math


def tuple_of_two(t):
    try:
        x = int(t.split(',')[0])
        y = int(t.split(',')[1])
        tup = (x, y)

        return tup
    except:
        raise argparse.ArgumentTypeError("Not a tuple of two ints, try again i guess...")

def handle_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--time", type=int, default=10000,
            help="The number of seconds to generate traffic for")

    parser.add_argument("-r", "--request_arrival_rate", type=float, default=0.3,
            help="Average inter arrival time between requests, in seconds")

    parser.add_argument("-u", "--request_arrival_rate_phase_2", type=float,
            default=None,
            help="Set the 2nd phase request arrival rate " +
                 "(if absent, continues phase 1)")

    parser.add_argument("-a", "--request_range", type=tuple_of_two, default=(4,7),
            help="Uniform distribution range for request quantities")

    parser.add_argument("-b", "--restock_amount", type=int, default=1000,
            help="Amount to restock when we restock")

    parser.add_argument("-l", "--restock_limit", type=int, default=20,
            help="When we have less than this, we restock 'restock_amount'")

    parser.add_argument("-x", "--no-restock", action='store_true', help="Never restock")

    parser.add_argument("-f","--filename", type=str, default='test_script.csv',
            help="Name for output csv file")

    parser.add_argument("-S","--seed", type=int, default=1,
            help="Seed for PRNG")
    return parser.parse_args()

def main():
    args = handle_arguments()
    random.seed(args.seed)
    with open(args.filename, mode='w', newline='') as f:
        writer = csv.writer(f)
        # start with a restock
        writer.writerow(['+', 0.0, args.restock_amount])
        next_request = random.expovariate(1 / args.request_arrival_rate)
        inventory = args.restock_amount
        while next_request <= args.time:
            inter_arrival_time = args.request_arrival_rate
            # if in phase 2, adjust IAT
            if next_request > args.time / 2 and args.request_arrival_rate_phase_2:
                inter_arrival_time = args.request_arrival_rate_phase_2
            # figure out if we do a restock or a request next
            if (not args.no_restock) and inventory <= args.restock_limit:
                # do restock
                writer.writerow(['+', next_request, args.restock_amount])
                inventory += args.restock_amount
                next_request = next_request + random.expovariate(1 / inter_arrival_time)
            # do request
            quantity = random.randrange(*args.request_range)
            writer.writerow(['-', next_request, quantity])
            next_request = next_request + random.expovariate(1 / inter_arrival_time)
            inventory -= quantity

main()
