"""
Generates runtime script
"""

import csv
import random

RANDOM_SEED = 1

# number records to generate
NUM_RECORDS = 10000

# avg inter-arrival time between requests, seconds
REQUEST_ARRIVAL_RATE = 0.3

# uniform-distribution range for request quantities (upper bound exclusive)
REQUEST_RANGE = (1, 10)

# avg inter-arrival time between restocks, seconds
RESTOCK_ARRIVAL_RATE = 100

# uniform-distribution range for request restocks
RESTOCK_RANGE = (2000, 2100)

# output file name
FNAME = 'test_script.csv'

def main():
    random.seed(RANDOM_SEED)
    with open(FNAME, mode='w', newline='') as f:
        writer = csv.writer(f)
        # start with a restock
        writer.writerow(['+', 0.0, random.randrange(*RESTOCK_RANGE)])
        next_restock = random.expovariate(1 / RESTOCK_ARRIVAL_RATE)
        next_request = random.expovariate(1 / REQUEST_ARRIVAL_RATE)
        for _ in range(NUM_RECORDS):
            # figure out if we do a restock or a request next
            if next_restock < next_request:
                # do restock
                writer.writerow(['+', next_restock, random.randrange(*RESTOCK_RANGE)])
                next_restock = next_restock + random.expovariate(1 / RESTOCK_ARRIVAL_RATE)
            else:
                # do request
                writer.writerow(['-', next_request, random.randrange(*REQUEST_RANGE)])
                next_request = next_request + random.expovariate(1 / REQUEST_ARRIVAL_RATE)

    
main()