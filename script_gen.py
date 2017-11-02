#!/usr/bin/python3
"""
Generates runtime script
"""

import argparse
import csv
import random

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
    parser.add_argument("-n", "--num_records", type=int, default=10000,
            help="The number of records to generate")
    parser.add_argument("-r", "--request_arrival_rate", type=float, default=0.3,
            help="Average inter arrival time between requests, in seconds")
    parser.add_argument("-a", "--request_range", type=tuple_of_two, default=(1,10),
            help="Uniform distribution range for request quantities")
    parser.add_argument("-s", "--restock_arrival_rate", type=float, default=100,
            help="Average inter arrival time between restocks, in seconds")
    parser.add_argument("-b", "--restock_range", type=tuple_of_two, default=(2000, 2100),
            help="Uniform distribution range for request restocks")
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
        writer.writerow(['+', 0.0, random.randrange(*args.restock_range)])
        next_restock = random.expovariate(1 / args.restock_arrival_rate)
        next_request = random.expovariate(1 / args.request_arrival_rate)
        for _ in range(args.num_records):
            # figure out if we do a restock or a request next
            if next_restock < next_request:
                # do restock
                writer.writerow(['+', next_restock, random.randrange(*args.restock_range)])
                next_restock = next_restock + random.expovariate(1 / args.restock_arrival_rate)
            else:
                # do request
                writer.writerow(['-', next_request, random.randrange(*args.request_range)])
                next_request = next_request + random.expovariate(1 / args.request_arrival_rate)


main()
