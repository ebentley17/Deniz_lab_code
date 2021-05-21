"""A package for handling data from instruments in the Deniz lab at Scripps.

Contents
--------
b2core_plate_fluorimeter/
    b2core_plate_fluorimeter.py
fluorimeter/
    corrections/
    fluorimeter.py
nanodrop/
    nanodrop.py
bokeh_scatter.py
utilities.py


The following files are not imported by default:

nanodrop_tests/
tutorials/
    handle_input.py

The following files can be accessed in the repo at 
https://github.com/ebentley17/Deniz_lab_code:

tutorials/
    sample_data/
    Fluorimeter Guide.ipynb
    Nanodrop Guide for Non-Coders.ipynb
"""

from . import bokeh_scatter, utilities
from wrangling.b2core_plate_fluorimeter import b2core_plate_fluorimeter
from wrangling.fluorimeter import fluorimeter
from wrangling.nanodrop import nanodrop

__version__ = "2.0.0"
__author__ = "Emily Bentley"