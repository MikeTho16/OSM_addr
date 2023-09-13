#!/usr/bin/python3
import re
import copy
import csv
import os
import sys

#addr_input = 'VirginiaSiteAddressPoint.txt'

# Put all of the street type abbreviations to be expanded here
# Note that the USPS has a standard list of such abbreviations
# This list (Python dictionary) is not complete, but it works
# for Rockbridge County
street_types = {
    'RD': 'Road',
    'TRL': 'Trail',
    'LN': 'Lane',
    'DR': 'Drive',
    'AVE': 'Avenue',
    'WAY': 'Way',
    'CIR': 'Circle',
    'RUN': 'Run',
    'HWY': 'Highway',
    'TPKE': 'Turnpike',
    'LOOP': 'Loop',
    'PL': 'Place',
    '': '',
    'CT': 'Court',
    'ST': 'Street',
    'PIKE': 'Pike',
    'HOLW': 'Hollow',
    'ROW': 'Row',
    'SPUR': 'Spur',
    'PARK': 'Park',
    'SQ': 'Square',
    'CRK': 'Creek',
    'VW': 'View',
    'TER': 'Terrace',
    'BLVD': 'Boulevard',
    'HTS': 'Heights',
    'ALY': 'Alley',
    'PATH': 'Path',
    'STA': 'Station',
    'PKWY': 'Parkway',
    'IS': 'Island',
    'RDG': 'Ridge',
    'XING': 'Crossing',
    'PT': 'Point',
    'CV': 'Cove',
    'GRN': 'Green',
    'MNR': 'Manor',
    'MDWS': 'Meadows',
    'HL': 'Hill',
    'BR': 'Branch',
    }

# The following should probably be expanded to include NW, SW, etc., but this
# seems sufficient for Rockbridge County
street_prefixes = {
    '': '',
    'N': 'North',
    'S': 'South',
    'E': 'East',
    'W': 'West'
    }

street_suffixes = {
    '': '',
    'N': 'North',
    'W': 'West',
    'E': 'East',
    'S': 'South'
    }

# A dictionary of all unit labels and their replacements
# This is sufficient for Rockbridge County, but will have to be expanded for
# other areas.
unit_labels = {
    'APT': 'Apartment',
    'BSMT': 'Basement',
    'STE': 'Suite',
    'STO': 'Stop',       # Not the official abbreviation
    'OFF': 'Office'      # Not the official abbreviation
    }

# The position of a word within the street name impacts how we handle it. For example
# if 'THE' appears as the first work in a street name we want it to be translated
# as 'The', but if appears elsewhere, we want to be translated as 'the'.  All comparisons
# are case insensitive, so for consistency, all patters use upper case letters.  Of
# course the substitutions are case sensitive - otherwise this wouldn't achieve the
# desired outcome.
#
# In the regular expression, the part between ( and ) is the part that gets replaced.
#
# \b - Represents a word boundary so '\b(AND)\b' only matches 'AND' if it is a stand alone
#      word, and doesn't match 'SAND' or 'ANDERSON'.  The word boundary can be the beginning
#      or end of the street name as well as most non alphanumeric characters.
street_name_special_cases = [
    (r' (THE)\b', 'the'),    # Only lowercase 'The' that doesn't occur at start
    (r'\b(ST) ', 'Saint'),   # Only translate ST -> Saint if it doesn't occur at the end of the name
    (r'\b(MTN)\b', 'Mountain'),
    (r'\b(MCCLUNG)\b', 'McClung'),
    (r'\b(MCCLURE)\b', 'McClure'),
    (r'\b(MCCORKLE)\b', 'McCorkle'),
    (r'\b(MCCORMICK)\b', 'McCormick'),
    (r'\b(MCCOWN)\b', 'McCown'),
    (r'\b(MCCRAY)\b', 'McCray'),
    (r'\b(MCCRORYS)\b', 'McCrorys'),
    (r'\b(MCCULLOCH)\b', 'McCulloch'),
    (r'\b(MCCURDY)\b', 'McCurdy'),
    (r'\b(MCDANIELS)\b', 'McDaniels'),
    (r'\b(MCELWEE)\b', 'McElwee'),
    (r'\b(MCFADDIN)\b', 'McFaddin'),
    (r'\b(MCKENDREE)\b', 'McKendree'),
    (r'\b(MCKENNY)\b', 'McKenny'),
    (r'\b(MCKETHAN)\b', 'McKethan'),
    (r'\b(MACKEYS)\b', 'McKeys'),
    (r'\b(LN)\b', 'Lane'),
    (r'\b(EXT)\b', 'Extension'),
    (r'\b(OF)\b', 'of'),
    (r'\b(AND)\b', 'and'),
    (r'\b(MT)\b', 'Mount'),
    (r'\b(HWY)\b', 'Highway'),
    (r'\b(MCCAULEY)\b', 'McCauley'),
    (r'\b(MCCLURES)\b', 'McClures'),
    (r'\b(MCBRYDGE)\b', 'McBrydge'),
    (r'\b(MCCUE)\b', 'McCue'),
    (r'\b(MCCUTCHEN)\b', 'McCutchen'),
    (r'\b(MCGUSLIN)\b', 'McGuslin'),
    (r'\b(MCILWEE)\b', 'McIlwee'),
    (r'\b(MCKAMY)\b', 'McKamy'),
    (r'\b(MCKINLEY)\b', 'McKinley'),
    (r'\b(WM)\b', 'William'),
    (r'\b(MACARTHUR)\b', 'MacArthur'),
    (r'\b(MACLAREN)\b', 'MacLaren'),
    (r'\b(MCALLIFF)\b', 'McAlliff'),
    (r'\b(MCCARTY)\b', 'McCarty'),
    (r'\b(MCCONAHEY)\b', 'McConahey'),
    (r'\b(MCCRAE)\b', 'McCrae'),
    (r'\b(MCDANIEL)\b', 'McDaniel'),
    (r'\b(MCDEARMON)\b', 'McDearmon'),
    (r'\b(MCFALLS)\b', 'McFalls'),
    (r'\b(MCGHEE)\b', 'McGhee'),
    (r'\b(MCINTOSH)\b', 'McIntosh'),
    (r'\b(MCKEEVER)\b', 'McKeever'),
    (r'\b(MCKNIGHTS)\b', 'McKnights'),
    (r'\b(MCMANAWAY)\b', 'McManaway'),
    (r'\b(MCVEY)\b', 'McVey'),
    (r'\b(MCGUIRE)\b', 'McGuire'),
    (r'\b(W\*)\Z', 'Way'),                   # Replaces 'W*' at the end of a string with 'Way'
    (r'\b(C\*)\Z', 'Circle'),
    (r'\b(A\*)\Z', 'Avenue'),
    (r'\b(H\*)\Z', 'Hollow'),
    (r'\b(T\*|TP)\Z', 'Turnpike'),
    (r'\b(X\*)\Z', 'Crossing')
    ]

def fix_street_name(street_name):
    """ 'Fixes' the street name, including:
        * Converting from all upper case to title case
        * Handling upper case in the middle of words, e.g. McDonald
        * Handling words that should be all upper case, e.g. IBM
    """
    street_name_temp = title_case(street_name)
    for case in street_name_special_cases:
        pat = re.compile(case[0], flags=re.IGNORECASE)
        street_name_temp = apply_case(pat, case[1], street_name_temp)
    return street_name_temp

def apply_case(pat, replacement, string_in):
    """ For every case where the regular expression pattern (pat)
    matches in string_in, replace group 1 with replacement.
    """
    string_out = ''
    start_pos = 0
    for match in pat.finditer(string_in):
        string_out += string_in[start_pos:match.start(1)] + replacement
        start_pos = match.end(1)
    string_out += string_in[start_pos:]
    return string_out

def make_addr_unit_and_label(unitid):
    """ Makes the addr:unit tag/field and the addr:unit:label tag/field.
    """
    label = ''
    unit = unitid
    for unit_type in unit_labels:
        if unit_type in unit:
            unit = unit.replace(unit_type,'').strip()
            label = unit_labels[unit_type].strip()
            break
    return label, unit

def make_addr_housenumber(preaddrnum, addrnum, addrnumsuf):
    """ Makes the addr:housenumber tag/field by concatenating the preaddrnum, addrnum
    and addrnumsuf from the input data.
    """
    return preaddrnum.strip() + addrnum.strip() + addrnumsuf.strip()

def make_addr_street(street_prefix, street_name, street_type, street_suffix):
    """ Makes the addr:street tag/field by modifying and combining fields
    from the input file.
    """
    street_prefix_expanded = expand_street_prefix(street_prefix)
    street_name_title_case = fix_street_name(street_name)
    street_type_expanded = expand_street_type(street_type)
    street_suffix_expanded = expand_street_suffix(street_suffix)
    addr_street = street_prefix_expanded
    if addr_street != '':
        addr_street = addr_street + ' '
    addr_street = addr_street + street_name_title_case
    if street_type_expanded != '' and street_type_expanded is not None:
        addr_street += ' ' + street_type_expanded
    if street_suffix_expanded != '' and street_suffix_expanded is not None:
        addr_street += ' ' + street_suffix_expanded
    return addr_street

def title_case(title):
    """ Sets the first character in each word in the given title to upper
    case, and the rest to lower case.  While Python does have a built in
    .title() function, it produces things like "2Nd Street" rather than
    "2nd Street".
    """
    title_fixed = ''
    for word in title.split():
        word_fixed = word[0:1].upper() + word[1:].lower()
        if title_fixed:
            title_fixed += ' '
        title_fixed += word_fixed
    return title_fixed

def expand_street_suffix(street_suffix):
    """ Expands abbreviations in the street suffix field. The field is considered
    as a whole. If the contents of the street suffix field is not recognized as
    an abbreviation, a message is printed to stdout.
    """
    if street_suffix in street_suffixes:
        return street_suffixes[street_suffix]
    print('unhanded street suffix: ' + street_suffix)
    return None

def expand_street_prefix(street_prefix):
    """ Expands abbreviations in the street prefix field.  The field is considered
    as a whole. if the contents of the street prefix field is not blank, and is
    not recognized as an abbreviation, a message is printed to stdout.
    """
    if street_prefix in street_prefixes:
        return street_prefixes[street_prefix]
    print('unhanded street prefix: ' + street_prefix)
    return None

def expand_street_type(street_type_abbr):
    """ Expands abbreviations in the street type field.  The field is considered
    as a whole.  If the contents of the street type field is not blank, and is
    not recognized as an abbreviation, a message is printed to stdout.
    """
    if street_type_abbr in street_types:
        return street_types[street_type_abbr]
    print('unhandled street type abbreviation:' + street_type_abbr)
    return None


def summarize(addr_input):
    """ Makes a unique list of addr:street, addr:city, addr:unit
    """
    with open(addr_input, newline='') as csvfile:
        addr_reader = csv.DictReader(csvfile)
        streets = {}
        cities = {}
        units = {}
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
            count += 1
    streets = list(streets.keys())
    streets.sort()
    for street in streets:
        print(street)
    print()

    cities = list(cities.keys())
    cities.sort()
    for city in cities:
        print(city)
    print()

    units = list(units.keys())
    units.sort()
    for unit in units:
        print(unit)

    print(f'Total Records: {count}')

def main():
    addr_input = sys.argv[1]
    summarize(addr_input)

if __name__ == '__main__':
    main()
