#!/usr/bin/python3
""" Tool to help QC the address data.  Currently it simply summarizes the address
tags in the file.  This makes it easier to spot problem.  Future plans are to
add some explicit QC checks.

Usage:
$ python3 addr_qc.py input_file_prep.csv

"input_file_prep.csv" must be a csv file where the fields correspond to OSM address
tags, e.g. addr:street.

Output:
Summary of contents of the input file printed to stdout.
"""
import csv
import sys


def summarize(addr_input):
    """ Makes a unique list of addr:street, addr:city, addr:unit
    """
    with open(addr_input, newline='',  encoding='utf-8') as csvfile:
        addr_reader = csv.DictReader(csvfile)
        streets = {}
        cities = {}
        units = {}
        unit_labels = {}
        count = 0
        for row in addr_reader:
            addr_street = row['addr:street']
            if addr_street not in streets:
                streets[addr_street] = addr_street
            if addr_street is None or addr_street == '':
                print('BLANK Street')
            addr_city = row['addr:city']
            if addr_city not in cities:
                cities[addr_city] = addr_city
            addr_unit = row['addr:unit']
            if addr_unit not in units:
                units[addr_unit] = addr_unit
            addr_unit_label = row.get('addr:unit:label','')
            if addr_unit_label not in unit_labels:
                unit_labels[addr_unit_label] = addr_unit_label
            count += 1
    print('Summary of addr:street')
    streets = list(streets.keys())
    streets.sort()
    for street in streets:
        print(street)
    print()

    print('Summary of addr:city')
    cities = list(cities.keys())
    cities.sort()
    for city in cities:
        print(city)
    print()

    print('Summary of addr:unit')
    units = list(units.keys())
    units.sort()
    for unit in units:
        print(unit)
    print()

    print('Summary of addr:unit:label')
    unit_labels = list(unit_labels.keys())
    unit_labels.sort()
    for unit_label in unit_labels:
        print(unit_label)
    print()

    print(f'Total Records: {count}')

def main():
    """ Main function.  Gets command line arguments and executes rest of the
    program.
    """
    addr_input = sys.argv[1]
    summarize(addr_input)

if __name__ == '__main__':
    main()
