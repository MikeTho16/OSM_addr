#!/usr/bin/python3
"""Prepares an address file that is in the standard text (csv) format provided
by the state of Virginia for import into OSM.  Unlike earlier versions of this
program, the entire file is processed.  If you wish to work with only one
county (recommended) you first need to split that county's addresses from the
main file using addr_split.py.

Usage:
$ python3 addr_prep.py input_file_raw.csv

Output:
input_file_prep.csv

To create the name of the output file "raw" is removed from the name of the
input file and replaced with "prep"

"""
import argparse
import re
import csv
import os
import yaml

street_types = {}
street_prefixes = {}
street_suffixes = {}
unit_labels = {}
unit_labels_stand_alone = {}
street_name_special_cases = []

def get_conf():
    """ Gets configuration information from the configuration file
    """
    # pylint: disable=W0603, C0103
    global street_types
    global street_prefixes
    global street_suffixes
    global unit_labels
    global unit_labels_stand_alone
    global street_name_special_cases
    with open('addr_prep.conf', 'r', encoding='utf-8') as conf_in:
        conf2 = yaml.load(conf_in, Loader=yaml.SafeLoader)
        street_types = conf2['street_types']
        street_prefixes = conf2['street_prefixes']
        street_suffixes = conf2['street_suffixes']
        unit_labels = conf2['unit_labels']
        unit_labels_stand_alone = conf2['unit_labels_stand_alone']
        street_name_special_cases = conf2['street_name_special_cases']

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

def make_addr_unit_and_label(unittype, unitid):
    """ Makes the addr:unit tag/field and the addr:unit:label tag/field.
    """
    if (unittype is None or unittype.strip() == '') and (unitid is None or unitid.strip() == ''):
        return '', ''
    if (unittype is None or unittype.strip() == ''):
        label, unit =  get_unit_and_label_from_unit(unitid.upper())
        return label, unit
    return get_unit_and_label(unittype.upper(), unitid.upper())

def get_unit_and_label(unittype, unitid):
    """ Gets the unit id and label assuming they are in separate fields in the input data
    """
    label = unittype
    unit = unitid
    if unittype in unit_labels:
        label = unit_labels[unittype]
        if unitid in unit_labels_stand_alone:
            unit = unit_labels_stand_alone[unitid]
        else:
            unit = unitid
    elif unittype in unit_labels_stand_alone:
        label = ''
        unit = unit_labels_stand_alone[unittype]
    return label, unit

def get_unit_and_label_from_unit(unitid):
    """ Gets both the unit and label from the unit field
    """
    label = ''
    unit = unitid
    found = False
    for unit_label, unit_label_expanded in unit_labels.items():
        if unit_label in unit:
            unit = unit.replace(unit_label,'').strip()
            label = unit_label_expanded.strip()
            found = True
            break
    if found:
        return label, unit
    # Stand alone unit labels
    # Stand alone unit labels go in the unit field, provided there is no
    # unitid (which there should not be)
    if unit in unit_labels_stand_alone:
        return '', unit_labels_stand_alone[unit]
    # Just in case a stand alone unit label has a unitid too
    for unit_label, unit_label_expanded in unit_labels_stand_alone.items():
        if unit_label in unit:
            unit = unit.replace(unit_label,'').strip()
            label = unit_label_expanded.strip()
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
    # Force the first character to be upper case. We can't do this earlier in
    # the process since addr:street may have a prefix
    addr_street = addr_street[0:1].upper() + addr_street[1:]
    # Remove any double spaces in addr:street
    addr_street = ' '.join(addr_street.split())
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

def main():
    """ Main function, gets the command line argument, and converts the specified
    file to one suitable for import to OSM.
    """
    get_conf()
    parser = argparse.ArgumentParser(description='Prepares address file for import to OSM.')
    parser.add_argument('input_file', help='file containing address info')
    args = parser.parse_args()
    addr_input = args.input_file
    addr_output, _ = os.path.splitext(addr_input)
    addr_output = addr_output.replace('_raw','')
    addr_output = addr_output + '_prep.csv'
    with open(addr_input, newline='', encoding='utf-8') as csvfile:
        with open(addr_output, 'w', newline='', encoding='utf-8') as csvfile_out:
            field_names = ['name', 'addr:housenumber', 'addr:street', 'addr:unit:label',
                           'addr:unit', 'addr:city', 'addr:state', 'addr:postcode',
                           'latitude', 'longitude']
            writer = csv.DictWriter(csvfile_out, fieldnames=field_names)
            writer.writeheader()
            addr_reader = csv.DictReader(csvfile)
            for row in addr_reader:
                addr_street = make_addr_street(
                    row['STREET_PREFIX'],
                    row['STREET_NAME'],
                    row['STREET_TYPE'],
                    row['STREET_SUFFIX'])
                if addr_street is None or addr_street == '':
                    print('BLANK Street')
                addr_city = row['PO_NAME'].title()
                # Reduce multiple spaces between words to single space
                addr_city = ' '.join(addr_city.split())
                addr_unit_label, addr_unit = make_addr_unit_and_label(row['UNITTYPE'],
                                                                      row['UNITID'])
                writer.writerow({'name': row['PLACENAME'].title(),
                                 'addr:housenumber': make_addr_housenumber(row['PREADDRNUM'],
                                                                           row['ADDRNUM'],
                                                                           row['ADDRNUMSUF']),
                                 'addr:street': addr_street,
                                 'addr:unit:label': addr_unit_label,
                                 'addr:unit': addr_unit,
                                 'addr:city': addr_city,
                                 'addr:state': 'VA',
                                 'addr:postcode': row['ZIP_5'],
                                 'latitude': row['LAT'],
                                 'longitude': row['LONG']})

if __name__ == '__main__':
    main()
