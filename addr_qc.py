#!/usr/bin/python3
""" addr_qc - Address QC
Takes as input a .osm file of addresses, and performs a number of quality checks
on them.  Any findings are printed to stdout.  A summary of postcodes, cities,
street names, and units is also printed to stdout, and this can be useful in
reviewing the data.

If you provide this program a database of zipcodes it will check if the postcodes
in the data are valid. You can download such a database from:
https://www.unitedstateszipcodes.org/zip-code-database/

Usage
$ python3 addr_qc addresses.osm

Under Linux you can create a symbolic link to this file so that you can execute
if from anywhere on your system.
* Open a terminal and navigate to ~/.local/bin
* $ ln -s /path_to_this_file/addr_qc.py addr_qc
"""
from xml.etree import ElementTree
import argparse
import csv
import re

class CountingSet():
    """ A class that acts like a set, but that keeps track of how many of each
    value has been added to the set
    """
    def __init__(self):
        self._dict = {}
        self.total_count = 0

    def __getattr__(self, item):
        return self._dict[item]

    def add(self, item):
        """ Add the specified item to the set.  If the item already exists in
        the set, its counter is incremented.  If the item does not exist in the
        set, it is added with its counter set to 1.
        """
        if item in self._dict:
            self._dict[item] = self._dict[item] + 1
        else:
            self._dict[item] = 1
        self.total_count += 1

    def items(self):
        """ A generator function that yeilds items and a count of how many times
        they were added to the set.
        """
        for k, v in self._dict.items():
            yield k, v

    def __len__(self):
        return len(self._dict)


def get_value(key, element):
    """ Given an OSM element, and a key, returns the value of that key, or None
    if the element doesn't have that key.
    """
    for child in element:
        if child.tag == 'tag':
            if 'k' in child.attrib:
                k = child.attrib['k']
                if k == key:
                    if 'v' in child.attrib:
                        return child.attrib['v']
    return None

def get_id(element):
    """ Given an OSM element, return it's id
    """
    return element.attrib['id']

def get_lat_lon(element):
    """ Given an OSM node, return it's latitude and longitude
    """
    if 'lat' in element.attrib:
        lat = float(element.attrib['lat'])
    else:
        lat = None
    if 'lon' in element.attrib:
        lon = float(element.attrib['lon'])
    else:
        lon = None
    return lat, lon

def main():
    """ Main function
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("in_file",
                        help="An .osm file containing addresses which is to be tested")
    args = parser.parse_args()
    zips = {}
    with open('zip_code_database.csv', newline='', encoding='utf-8') as csvfile:
        zip_reader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
        for row in zip_reader:
            zipcode = row['zip']
            cities = row['acceptable_cities'].split(',')
            cities.append(row['primary_city'])
            cities = [x.strip().upper() for x in cities]
            zips[zipcode] = {'cities': cities, 'type': row['type']}
    tree = ElementTree.parse(args.in_file)
    root = tree.getroot()
    cities = CountingSet()
    postcodes = CountingSet()
    streets = CountingSet()
    addrs = CountingSet()
    all_errors = CountingSet()
    locations = CountingSet()
    units =  set()
    for child in root:
        if child.tag != 'node':
            continue
        # only look at new nodes
        if int(get_id(child)) >= 0:
            continue
        errors = []
        city = get_value('addr:city', child)
        if city:
            city = city.strip()
        street = get_value('addr:street', child)
        if street:
            street = street.strip()
        postcode = get_value('addr:postcode', child)
        housenumber = get_value('addr:housenumber', child)
        unit = get_value('addr:unit', child)
        addrs.add((housenumber.upper() if housenumber else None,
                   street.upper() if street else None,
                   city.upper() if city else None,
                   postcode.upper() if postcode else None,
                   unit.upper() if unit else None))
        lat, lon = get_lat_lon(child)
        locations.add((lat, lon))
        # Coordinate checks
        if lat is None or lon is None:
            msg = 'Coordinates, null or missing'
            errors.append(msg)
            all_errors.add(msg)
        elif lat in (-90.0, 90.0):
            msg = 'Coordinates, suspect, at North or South Pole'
            errors.append(msg)
            all_errors.add(msg)
        elif lat < -90.0 or lat > 90.0 or lon < -180.0 or lon > 180.0:
            msg = 'Coordinates, off Earth'
            errors.append(msg)
            all_errors.add(msg)
        elif lon in (180.0, -180.00):
            msg = 'Coordinates, suspect, on antimeridian'
            errors.append(msg)
            all_errors.add(msg)
        elif lon == 0 and lat == 0:
            msg = 'Coordinates, suspect, on Null Island (0, 0)'
            errors.append(msg)
            all_errors.add(msg)
        # City checks
        if not city:
            msg = 'City, missing'
            errors.append(msg)
            all_errors.add(msg)
        else:
            cities.add(city)
            if not re.search(r'^[A-Z]', city) or re.search(r'[A-Z]{2}', city):
                msg = 'City, invalid capitalization'
                errors.append(msg)
                all_errors.add(msg)
            if re.search(r'[^ -~]', city):
                msg = 'City, contains non printable characters'
                errors.append(msg)
                all_errors.add(msg)
            if re.search(r';', city):
                msg = "City, possible multiple values separated by ';'"
                errors.append(msg)
                all_errors.add(msg)
        # Housenumber checks
        if not housenumber:
            msg = 'Housenumber, missing'
            errors.append(msg)
            all_errors.add(msg)
        else:
            if re.search(r'PO BOX', housenumber.upper()):
                msg = 'Housenumber, PO Box not a valid housenumber'
                errors.append(msg)
                all_errors.add(msg)
            if re.search(r';', housenumber):
                msg = "Housenumber, possible multiple values separated by ';'"
                errors.append(msg)
                all_errors.add(msg)
            if re.search(r'[^ -~]', housenumber):
                msg = 'Housenumber, contains non printable characters'
                errors.append(msg)
                all_errors.add(msg)
        # Postcode checks
        if not postcode:
            msg = 'Postcode, missing'
            errors.append(msg)
            all_errors.add(msg)
        else:
            postcodes.add(postcode)
            if not re.search(r'^[0-9]{5}$', postcode):
                msg = 'Postcode, Invalid, must be exactly five numeric digits'
                errors.append(msg)
                all_errors.add(msg)
            elif postcode not in zips:
                msg = 'Postcode, valid format, but not in postal database'
                errors.append(msg)
                all_errors.add(msg)
            else:
                if zips[postcode]['type'] == 'PO BOX':
                    msg = 'Postcode, valid format, but only valid for PO Boxes'
                    errors.append(msg)
                    all_errors.add(msg)
                if city:
                    for split_city in city.split(';'):
                        if split_city.upper().strip() not in zips[postcode]['cities']:
                            msg = 'Postcode, valid format, but does not correspond to city'
                            errors.append(msg)
                            all_errors.add(msg)
        # Street checks
        if not street:
            msg = 'Street, missing'
            errors.append(msg)
            all_errors.add(msg)
        else:
            streets.add(street)
            if not re.search(r'^[A-Z1-9]', street) or re.search(r'[A-Z]{2}', street):
                msg = 'Street, invalid capitalization'
                errors.append(msg)
                all_errors.add(msg)
            if re.search(r'^[WENS]\b', street):
                msg = 'Street, unexpanded abbreviation at start'
                errors.append(msg)
                all_errors.add(msg)
            if re.search(r'/b[WENS]\.?$', street):
                msg = 'Street, unexpanded abbreviation at end'
                errors.append(msg)
                all_errors.add(msg)
            if re.search(r';', street):
                msg = "Street, possible multiple ';' separated values"
                errors.append(msg)
                all_errors.add(msg)
            if re.search(r'(\b\S+\b)\s+\b\1\b', street):
                msg = 'Street, repeated word'
                errors.append(msg)
                all_errors.add(msg)
            if re.search(r'[^ -~]', street):
                msg = 'Street, contains non printable characters'
                errors.append(msg)
                all_errors.add(msg)
            if re.search(r'PO BOX', street.upper()):
                msg = 'Street, PO Box not a valid street'
                errors.append(msg)
                all_errors.add(msg)
        # Unit checks
        if unit:
            units.add(unit)
            if re.search(r'[^ -~]', unit):
                msg = 'Unit, contains non printable characters'
                errors.append(msg)
                all_errors.add(msg)
            if re.search(r';', unit):
                msg = "Unit, possible multiple ';' separated values"
                errors.append(msg)
                all_errors.add(msg)
        if errors:
            print(f'{repr(housenumber)} | {repr(street)} | {repr(city)} | {repr(postcode)} '
                  f'| {repr(unit)}')
            for error in errors:
                print('    ' + error)
    print()
    print('List of duplicate addresses')
    total_dups = 0
    dup_sets = 0
    for addr, count in addrs.items():
        if count > 1:
            dup_sets += 1
            total_dups += count
            addr_full = f'    {addr[0]} | {addr[1]} | {addr[2]} | {addr[3]} | {addr[4]}'
            print(f'    {addr_full:.<80}{count:.>5}')
    print()
    print('List of cities found in data')
    for city, count in sorted(cities.items(), key=lambda x: x[0].upper()):
        print(f'    {city:.<35}{count:.>5}')
    print()
    print('List postcodes found in data')
    for postcode, count in sorted(postcodes.items(), key=lambda x: x[0]):
        print(f'    {postcode:.<20}{count:.>5}')
    print()
    print('List of streets found in data')
    for street, count in sorted(streets.items(), key=lambda x: x[0].upper()):
        print(f'    {street:.<35}{count:.>5}')
    print()
    print('List of units found in data')
    for unit in sorted(units, key=lambda x: x.upper()):
        print(f'    {unit}')
    print()
    print('Duplicate Locations')
    for loc, count in locations.items():
        if count > 1:
            msg = f'Multiple features in same location {loc[0]}, {loc[1]}'
            print(f'    {msg:.<75}{count:.>5}')
    print()
    print('Error summary')
    for error, count in sorted(all_errors.items(), key=lambda x: x[0]):
        print(f'    {error:.<75}{count:.>5}')
    print(f'    {"Duplicate addresses, total features":.<75}{total_dups:.>}')
    print(f'    {"Duplicate addresses, sets":.<75}{dup_sets:.>5}')

if __name__ == '__main__':
    main()
