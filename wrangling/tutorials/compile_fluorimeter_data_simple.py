"""This is a simple script to compile data from the Deniz lab fluorimeter.

You can make a shortcut of this file. Double-click the file to run it. 
You will be prompted to enter the path for a  folder of .ifx data 
files. A .csv with the compiled data will be saved in the same folder. 
"""

import sys
import glob
import pandas
import numpy as np

from wrangling import fluorimeter, utilities
from wrangling.tutorials import handle_input


# prevent closing on exception
def show_exception_and_exit(exc_type, exc_value, tb):
    import traceback

    traceback.print_exception(exc_type, exc_value, tb)
    input("Press key to exit.")
    sys.exit(-1)


sys.excepthook = show_exception_and_exit


# set up input_manipulator function to pass to handle_input.interpret()
def validate_folder(string):
    if handle_input.file_or_folder(string) == "folder":
        return string
    else:
        raise RuntimeError("You have not selected a valid folder.\n")


# repeat the query if you don't select any files
valid_folder_selected = False
while not valid_folder_selected:
    filepath = handle_input.interpret(
        "Enter the path of the folder to be analyzed: ", 
        validate_folder
    )

    try:
        df = fluorimeter.assemble_ifx_files(
            glob.glob(filepath + "/*ifx"), 
            title_as_column=True
        )
        valid_folder_selected = True
    # if something goes wrong, show the error and repeat the loop
    except ValueError as e:
        print(str(e) + "\n")

# correct Intensity column if present
try:
    df = fluorimeter.correct_df_intensity(df, detect_slit=True)
# will fail if comment column is not an allowed slit value
except (KeyError, RuntimeError):
    pass

# df has been modified in place for the last time
# this is the version of df that gets imported by other scripts


def automatically_standardize_concentrations(df):
    # automatically detect columns with concentration entries
    concentration_columns = [x for x in df.columns if "[" in x]

    df = df.copy()

    # standardize concentration to the first unit found in each column
    for conc_col in concentration_columns:
        # iterate through rows looking for the first non-NaN value
        i = 0
        while i < len(df):
            column_content = df.loc[i, conc_col]

            if type(column_content) is float:
                if np.isnan(column_content):
                    i += 1
            else:
                break

        # this will cause an error if there is an entire column of NaN values
        # and i gets to the size of the dataframe
        # but an entire column of NaN shouldn't be constructed
        unit = str(column_content)[-2:]
        if unit not in ["mM", "uM", "nM", "pM"]:
            continue

        df = utilities.standardize_concentration(df, columns=conc_col, unit=unit)

    return df


automatically_standardize_concentrations(df).to_csv(filepath + "/compiled.csv")
