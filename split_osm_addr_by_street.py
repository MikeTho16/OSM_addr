#!/usr/bin/python3
""" split_osm_addr_by_street - Split a file of OSM addresses into separate file based upon
street name (addr:street).  Both the input and output files are in the .osm format.
"""
from xml.etree import ElementTree
import argparse
import os

def get_value(key, element):
    """ Given an OSM key and an xml element tree element, return the value of the key.

    Parameters:
        key - (in) The OSM key.
        element - (in) an xml ElementTree element.

    Returns:
        The value of the specified key, or if key isn't found, returns None
    """
    for child in element:
        if child.tag == 'tag':
            if 'k' in child.attrib:
                k = child.attrib['k']
                if k == key:
                    if 'v' in child.attrib:
                        return child.attrib['v']
    return None

def get_args():
    """ Gets the command line arguments that were present when program was
    invoked.

    Parameters:
        <none>

    Returns:
         An argparse.Namespace object containing the parameters passed on the
         command line.
    """
    parser = argparse.ArgumentParser(
        prog='split_osm_addr_by_street',
        description='Splits a .osm file containing addresses into separate files'
            'based on street name')
    parser.add_argument("in_file",
                        help="An .osm file containing addresses which is to be split")
    parser.add_argument("out_dir", help="directory in which to write the output files")
    return parser.parse_args()

def main():
    """ The main function.
    """
    args = get_args()
    tree = ElementTree.parse(args.in_file)
    root = tree.getroot()
    out={}
    for child in root:
        if child.tag == 'node':
            city = get_value('addr:city', child).strip().replace(' ','_')
            street = get_value('addr:street', child).strip().replace(' ', '_')
            if not street:
                file_name = 'NoStreet'
            if not city:
                city = 'NoCity'
            file_name = city + '__' + street
            file_name = os.path.join(args.out_dir, file_name + ".osm")
            if file_name not in out:
                # pylint: disable=R1732
                file_handle = open(file_name, 'w', encoding='utf-8')
                out[file_name] = file_handle
                file_handle.write("<?xml version='1.0' encoding='UTF-8'?>\n"
                    "<osm version='0.6' upload='never' download='never' "
                    "generator='JOSM'>\n")
            else:
                file_handle = out[file_name]
            file_handle.write(ElementTree.tostring(child).decode())
    for _, file_handle in out.items():
        file_handle.write("</osm>")
        file_handle.close()

if __name__ == '__main__':
    main()
