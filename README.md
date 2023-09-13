# OSM_addr
Tools for converting address data for import into OpenStreetMap

Currently this is specific to address data from the state of Virginia.  The basic workflow is:
* Split the addresses for the county of interest from the main file from the state of Virginia with addr_split.py
* Prepare the resulting county file by changing the fields to appropriate OSM tags with addr_prep.py
* QC file with addr_qc.py

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




  

