# Deniz_lab_code
This repo contains code written for the Deniz lab at Scripps Research. 

## Wrangling

The `wrangling` package contains three subpackages: `b2core_plate_fluorimeter`,
`fluorimeter`, and `nanodrop`, along with utilities code for use with all three 
instrument outputs.  

`wrangling/tutorials` includes two Jupyter notebooks: "Fluorimeter Guide" to help
users learn to use the fluorimeter package, and "Nanodrop Guide for Non-Coders" 
to allow users to process nanodrop data with no knowledge of python.

Unit tests for the `nanodrop` subpackage are provided in `nanodrop_tests`. The 
`fluorimeter` and `b2core_plate_fluorimeter` subpackages have not been tested as
thoroughly.

`wrangling` can be installed from the command line with 
`pip install git+https://github.com/ebentley17/Deniz_lab_code/`

## Other Files

`amino_acid_mutations.xlsx` allows users to identify amino acid mutations that
would result in a given change in protein molecular weight, to assist in 
analyzing mass spectromotry results.

<br>

### Version 2.0.0 Changelog

#### wrangling
- updated package structure. Subpackage names now match the names of the contained modules (`b2core_plate_fluorimeter`, `fluorimeter`, `nanodrop`) for improved importing behavior
- `nanodrop_tests` is now an independent subpackage, not imported by default
- tutorial materials are grouped together in the `tutorial` subpackage, not imported by default
- added setup.py to allow remote installation
- updated docstrings

#### wrangling/fluorimeter
- changed module name `fluorimeter_wrangling` to `fluorimeter`
- prevented dataframes from being changed in-place
- new functions:
    - `get_corrections` accesses newly included corrections files
    - `correct_df_intensity` applies intensity corrections to a dataframe
- `add_descriptor_data` 
    - allows the experiment title to be added to the dataframe with `title_as_column=True`
    - recognizes mM as a unit
    - fixed bug where files with varying wavelengths would gain a nonsense "em wavelength (nm)" column
- `assemble_ifx_files`
    - skips files without the .ifx suffix
    - passes the `title_as_column` kwarg to `add_descriptor_data`
- `break_out_variable`
    - prevents `variable` from being assigned a column name that already exists, as-is or with brackets
    - allows rows with zero valid entries
- `make_prism_data`
    - depracated kwargs `groupby_variable` and `index_variable`, replaced with `column_variable` and `row_variable`, respectively. Depracated kwargs will overwrite new default kwargs if used.
    - allows row_variable to be a list of columns
    - improved handling of float conversion
- `plot_averages` (depracated)
    - fixed bug where kwargs were overwritten with defaults when calling the function from utilities

#### wrangling/utilities
- new function: `standardize_concentration` makes all values match a specified unit
- `break_out_date_and_time`: depracated kwargs `breakout_column` and `date_time_split`; replaced with `column` and `split`, respectively. Depracated kwargs will overwrite new default kwargs if used.
- `plot_averages`: removed mutable default argument for `palette`
- `concentration_to_nM`: depracated in favor of `standardize_concentrations`

#### wrangling/tutorials
- wrote `Fluorimeter Guide`
- grouped tutorial files together
- updated name of `Guide for Non-Coders` to specify it works on nanodrop data

#### wrangling/b2core_plate_fluorimeter
- changed module name `b2core_plate_fluorimeter_wrangling` to `b2core_plate_fluorimeter`
- made underlying functions private

#### wrangling/nanodrop
- changed module name `tidy_data` to `nanodrop`
- changed function `run_all` to `tidy_data`

#### wrangling/nanodrop_tests
- `test_tidy_data.py` now works with relative paths to `test_data`