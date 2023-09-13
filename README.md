# OSM_addr
Tools for converting address data for import into OpenStreetMap

Currently this is specific to address data from the state of Virginia.  The basic workflow is:
* Split the addresses for the county of interest from the main file from the state of Virginia with addr_split.py
* Prepare the resulting county file by changing the fields to appropriate OSM tags with addr_prep.py
* QC file with addr_qc.py

General Setup
-------------
These programs make use of PyYAML and therefore it must be installed:
$ pip install PyYAML

addr_split.py
-------------
Usage: <br>
  $ python addr_split.py \<input file> \<county to extract>

The result is a new file:
\<county name>_raw.csv

addr_prep.py
------------
Usage: <br>
$ python addr_prep.py \<input file>



  

