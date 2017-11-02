"""
script_parser.py

parses a run-script for the inventory system

A script is a CSV file with three columns:
    type: '+' or '-', whether it's supplying, '+', or taking '-', supply
    time: float, timestamp of action
    quantity: int, quantity of item to stock or take

For example:
-, 0, 3
-, 0.5, 4
-, 1.3, 10

"""

import csv


class InventoryRequest:

    def __init__(self, timestamp, quantity, request_id):
        self.timestamp = timestamp
        self.quantity = quantity
        self.request_id = request_id

    def __repr__(self):
        return '<InventoryRequest' + \
                    ' ts=' + str(self.timestamp) + \
                    ' quantity=' + str(self.quantity) + \
                    ' id=' + str(self.request_id) + \
                '>'


class InventoryRestock:

    def __init__(self, timestamp, quantity, request_id):
        self.timestamp = timestamp
        self.quantity = quantity
        self.request_id = request_id

    def __repr__(self):
        return '<InventoryRestock' + \
                    ' ts=' + str(self.timestamp) + \
                    ' quantity=' + str(self.quantity) + \
                    ' id=' + str(self.request_id) + \
                '>'


def parse_script(fname):
    """
    Parses a script
    Params:
        fname: the file name of the script
    Returns:
        [InventoryRequest]
    """
    with open(fname) as f:
        reader = csv.reader(f)
        next_id = 0
        ret = []
        for line in reader:
            if line[0] == '-':
                ret.append(InventoryRequest(
                    float(line[1]),
                    int(line[2]),
                    next_id
                ))
            elif line[0] == '+':
                ret.append(InventoryRestock(
                    float(line[1]),
                    int(line[2]),
                    next_id
                ))
            next_id += 1
        return sorted(ret, key=lambda x: x.timestamp)
