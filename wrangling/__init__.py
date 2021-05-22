"""A package for handling data from instruments in the Deniz lab at Scripps.

Also available at https://github.com/ebentley17/Deniz_lab_code

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

Not Imported By Default
-----------------------
nanodrop_tests/
tutorials/
"""

from . import bokeh_scatter, utilities
from wrangling.b2core_plate_fluorimeter import b2core_plate_fluorimeter
from wrangling.fluorimeter import fluorimeter
from wrangling.nanodrop import nanodrop

__version__ = "2.0.1"
__author__ = "Emily Bentley"