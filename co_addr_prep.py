#!/usr/bin/python3.10
"""Prepares an address file from the state of Colorado that is in a file
geodatabase for import into OSM. Optionally, you can specify that you want
to remove addresses that already exist in OSM by providing a file containing
those addresses.

Usage:
$ python3 addr_prep.py input_file_raw.csv

Output:
input_file_prep.csv

To create the name of the output file "raw" is removed from the name of the
input file and replaced with "prep"

"""
import argparse
import re
from pathlib import Path
import pathlib
import xml.etree.ElementTree as ET
import yaml

from osgeo import ogr

street_types = {}
street_prefixes = {}
street_suffixes = {}
unit_labels = {}
unit_labels_stand_alone = {}
street_name_special_cases = []

def get_existing_addrs(existing_fname, target_city):
    """ Read a .osm file of existing OSM data and put the addresses
    in a set.

    Parameters:
        existing_fname = Name of file containing addresses already in OSM. File
            must be in .osm format.
        target_city = Name of city for which we are processing addresses.
    """
    if not existing_fname:
        return None
    addr_housenumber = ''
    addr_street = ''
    addr_city = ''
    addr_unit = ''
    count = 0
    element_stack = []
    existing_addrs = set()
    for event, elem in ET.iterparse(existing_fname, events=("start", "end")):
        count += 1
        if not count % 100000:
            print(count)
        if event == 'start':
            element_stack.append(elem)
        elif event == 'end':
            element_stack.pop()
            if elem.tag == 'tag':
                if 'k' in elem.attrib and 'v' in elem.attrib:
                    key = elem.attrib['k']
                    value = elem.attrib['v']
                    if key == 'addr:housenumber':
                        addr_housenumber = value
                    elif key == 'addr:street':
                        addr_street = value
                    elif key == 'addr:city':
                        addr_city = value
                    elif key == 'addr:unit':
                        addr_unit = value
            elif elem.tag in ('node', 'way', 'relation'):
                if not target_city or addr_city.upper() == target_city.upper():
                    existing_addrs.add((addr_city, addr_street, addr_housenumber, addr_unit))
                addr_housenumber = ''
                addr_street = ''
                addr_city = ''
                addr_unit = ''
            if element_stack:
                element_stack[-1].remove(elem)
    return existing_addrs

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
    source_path = Path(__file__).resolve()
    source_dir = source_path.parent
    print(source_dir)
    conf_fname = 'addr_prep.conf'
    if not Path(conf_fname).exists():
        pass
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

    Parameters:
        street_name - (in) The street name that is to be "fixed"

    Returns:
        The "fixed" street name.
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

def make_addr_unit_and_label_co(building, floor, unit):
    """ Makes the addr:unit tag/field and the addr:unit_label tag/field
    for a Colorado address
    """
    unitid = ''
    unittype = ''
    if building:
        unittype = 'Building'
        unitid = building
    if floor:
        if unitid:
            print('multiple units')
        else:
            unittype = 'Floor'
            unitid = floor
    if unit:
        if unitid:
            print('multiple units')
        else:
            unittype = 'Unit'
            unitid = unit
    return unittype, unitid

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

def make_addr_street_co(st_pre_mod, pre_dir, pre_type,
                        st_pre_sep, street_name, post_type, post_dir):
    """ Mkes the addr:street tag/field for a Colorado address by modifying and
    combining fields from the input file.
    """
    street_prefix_expanded = expand_street_prefix(pre_dir)
    street_name_title_case = fix_street_name(street_name)
    street_type_expanded = expand_street_type(post_type)
    street_suffix_expanded = expand_street_suffix(post_dir)
    addr_street = concat_with_space_if_not_null([st_pre_mod,
                                                 street_prefix_expanded,
                                                 pre_type,
                                                 st_pre_sep,
                                                 street_name_title_case,
                                                 street_type_expanded,
                                                 street_suffix_expanded])
    addr_street = fix_street_name(addr_street)
    # Force the first character to be upper case. We can't do this earlier in
    # the process since addr:street may have a prefix
    addr_street = addr_street[0:1].upper() + addr_street[1:]
    # Remove any double spaces in addr:street
    addr_street = ' '.join(addr_street.split())
    #addr_street = title_case(addr_street)
    return addr_street

def concat_with_space_if_not_null(list_to_concat):
    """ concatenates a list of strings into a new string with the individual
    elements separated by a space. There is probably a more pythonic way of
    doing this...
    """
    out_str = ''
    for item in list_to_concat:
        if item is not None and item != '':
            if out_str != '':
                out_str = out_str + ' ' + item
            else:
                out_str = item
    return out_str

def title_case(title):
    """ Sets the first character in each word in the given title to upper
    case, and the rest to lower case.  While Python does have a built in
    .title() function, it produces things like "2Nd Street" rather than
    "2nd Street".

    Parameters:
        title - (in) The string that is to be "title cased"

    Returns:
        The input string after it has been "title cased"
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

    Parameters:
        street_suffix - (int) The street suffix whose abbreviation is to be expanded.

    Returns:
        Either the street suffix with its abbreviation expanded, or None if it is not
        possible to expand the abbreviation.
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

def read_field(feature, field):
    """ Reads the value of the given field from the given feature.  If it is None,
    returns and empty string, otherwise returns the value.
    """
    value = feature.GetField(field)
    if not value:
        value = ''
    else:
        value = value.strip()
    return value

def get_args():
    """ Gets the command line arguments

    Parameters:
        (none)

    Returns:
        an argparse.Namespace object containing the parameters passed on the command line
    """
    parser = argparse.ArgumentParser(
        prog='co_addr_prep',
        description='Prepares Colorado addresses for import to OSM.')
    parser.add_argument('input_fgdb_and_layer', help='file geodatabase containing address info, '
                        'including the layer e.g. /path/to/fgdb/layer')
    parser.add_argument('output_file', help='output file to which to write the results'
                        ' in .osm format')
    parser.add_argument('--city', help='only writes addresses with the '
                        'indicated city to the output')
    parser.add_argument('--existing', help='file of existing OSM addresses which are not to be'
                        ' placed in the output file.')
    args = parser.parse_args()
    if args.city:
        args.city = args.city.upper()
    return args

def main():
    """ Main function, gets the command line argument, and converts the specified
    file to one suitable for import to OSM.
    """
    args = get_args()
    get_conf()
    existing_addrs = get_existing_addrs(args.existing, args.city)
    print(len(existing_addrs))
    #sys.exit()
    #source_path = Path(__file__).resolve()
    #source_dir = source_path.parent
    #print(source_dir)
    #sys.exit()
    driver = ogr.GetDriverByName("OpenFileGDB")
    path = pathlib.PurePath(args.input_fgdb_and_layer)
    layer = str(path.name)
    fgdb = str(path.parents[0])
    data_source = driver.Open(fgdb, 0)
    addr_layer = data_source.GetLayer(layer)
    with open(args.output_file, 'w', newline='', encoding='utf-8') as addr_out:
        addr_out.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        addr_out.write('<osm version="0.6" generator="JOSM">\n')
        node_id = -1
        for addr_feature in addr_layer:
            place_name = addr_feature.GetField('PlaceName')
            if args.city and place_name.upper() != args.city:
                continue
            geom = addr_feature.GetGeometryRef()
            point = geom.GetPoint(0)
            lat = point[1]
            lon = point[0]
            addr_num = read_field(addr_feature, 'AddrNum')
            #num_suf = read_field(addr_feature, 'NumSuf')
            st_pre_mod = read_field(addr_feature, 'St_PreMod')
            pre_dir = read_field(addr_feature, 'PreDir')
            pre_type = read_field(addr_feature, 'PreType')
            st_pre_sep = read_field(addr_feature, 'St_PreSep')
            street_name = read_field(addr_feature, 'StreetName')
            post_type = read_field(addr_feature, 'PostType')
            post_dir = read_field(addr_feature, 'PostDir')
            #st_pos_mod = read_field(addr_feature, 'St_PosMod')
            building = read_field(addr_feature, 'Building')
            floor = read_field(addr_feature, 'Floor')
            unit = read_field(addr_feature, 'Unit')
            zip_code = read_field(addr_feature, 'Zipcode')
            addr_street = make_addr_street_co(st_pre_mod, pre_dir, pre_type, st_pre_sep,
                                              street_name, post_type, post_dir)
            if not addr_street:
                print('BLANK Street')
            addr_city = place_name.title()
            # Reduce multiple spaces between words to single space
            addr_city = ' '.join(addr_city.split())
            addr_unit_label, addr_unit = make_addr_unit_and_label_co(building, floor, unit)
            if (addr_city, addr_street, addr_num, addr_unit) in existing_addrs:
                continue
            addr_out.write(f'    <node id="{node_id}" action="modify" visible="true" lat="{lat}" '
                           f'lon="{lon}">\n')
            addr_out.write(f'        <tag k="addr:housenumber" v="{addr_num}" />\n')
            addr_out.write(f'        <tag k="addr:street" v="{addr_street}" />\n')
            if addr_unit:
                addr_out.write(f'        <tag k="addr:unit" v="{addr_unit}" />\n')
                if addr_unit_label:
                    addr_out.write(f'        <tag k="addr:unit:label" v="{addr_unit_label}" />\n')
            addr_out.write(f'        <tag k="addr:city" v="{addr_city}" />\n')
            addr_out.write(f'        <tag k="addr:postcode" v="{zip_code}" />\n')
            addr_out.write('        <tag k="addr:state" v="CO" />\n')
            addr_out.write('    </node>\n')
            node_id -= 1
        addr_out.write('</osm>\n')

if __name__ == '__main__':
    main()
