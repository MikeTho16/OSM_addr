# OSM_addr
Tools for converting address data for import into OpenStreetMap

Currently this is specific to address data from the state of Virginia and Colorado.  

For VIrgina, the basic workflow is:
* Split the addresses for the county of interest from the main file from the state of Virginia with addr_split.py
* Prepare the resulting county file by changing the fields to appropriate OSM tags with addr_prep.py
* QC file with addr_qc.py

For Colorado, the basic workflow is:
* Download the latest addresses in File Geodatabase format from the State of Colorado.
* Use Overpass to download the current addresses for the city you are interested in from OSM
* Convert the addresses from the schema used by the State of Colorado to the OSM "schema" with co_addr_prep.py
* Split the results of the above into separate files for each street
* Create a Maproulette cooperative challenge with the MR command line interface


General Setup
-------------
These programs make use of PyYAML and therefore it must be installed:<br>
$ pip install PyYAML

All settings are now in the configuration file addr_prep.conf (written in YAML), therefore it is no longer necessary to edit the actual python code.

addr_split.py
-------------
Usage: <br>
  $ python addr_split.py \<input file> \<county to extract>

The result is a new file:<br>
\<county name>_raw.csv<br>

This file has the same structure as the input file, with the exception that latitude and longitude columns have been added. This allows the file to be loaded into JOSM for easy comparison with the converted file produced by addr_prep.py.


addr_prep.py
------------
Usage: <br>
$ python addr_prep.py \<input file> <br>

This file is a .csv file, but the field names are OSM tags, e.g. addr:street

addr_qc.py
----------
Usage: <br>
$ python addr_qc.py \<prep addr file>

Currently this just prints a summary of the contents of some of the tags in the input file to stdout.  This makes it easier to review the address file. 

co_addr_prep.py
---------------
    usage: co_addr_prep [-h] [--city CITY] [--existing EXISTING]
                    input_fgdb_and_layer output_file
    
    Prepares Colorado addresses for import to OSM.

    positional arguments:
      input_fgdb_and_layer  file geodatabase containing address info, including
                            the layer e.g. /path/to/fgdb/layer
      output_file           output file to which to write the results in .osm
                            format
    
    options:
      -h, --help            show this help message and exit
      --city CITY           only writes addresses with the indicated city to the
                            output
      --existing EXISTING   file of existing OSM addresses which are not to be
                            placed in the output file.





  

