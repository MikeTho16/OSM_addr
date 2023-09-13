#!/usr/bin/python3
import re
import copy
import csv
import sys


def main():
    addr_input = sys.argv[1]
    county = sys.argv[2]
    split_county(addr_input, county)

def split_county(addr_input, county):
    """ Makes a file of just the data from a single county.  The format is the same
    as that of the input file, with the exception that latitude and longitude are
    added so that the data can be visualized in JOSM.
    """
    out_file_name = county.lower().replace(' county','') + '_raw.csv'
    with open(addr_input, newline='') as csvfile:
        addr_reader = csv.DictReader(csvfile)
        with open(out_file_name, 'w', newline='') as csvfile_out:
            field_names = copy.deepcopy(addr_reader.fieldnames)
            field_names.append('latitude')
            field_names.append('longitude')
            writer = csv.DictWriter(csvfile_out, fieldnames=field_names)
            writer.writeheader()
            county = county.upper()
            for row in addr_reader:
                # Unlike the rest of the file, it seems that the 'MUNICIPALITY' field's
                # contents are in title case, but we don't take any chances and force
                # an uppercase comparison.
                if row['MUNICIPALITY'].upper() == county:
                    new_row = {}
                    for key, value in row.items():
                        new_row[key] = value
                    new_row['latitude'] = row['LAT']
                    new_row['longitude'] = row['LONG']
                    writer.writerow(new_row)




if __name__ == '__main__':


    #summarize()
    #split_county()
    main()
