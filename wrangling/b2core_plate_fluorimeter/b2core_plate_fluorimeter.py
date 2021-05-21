"""Functions to handle data output from the Biochemistry and Biophysics Core 
facility's plate fluorimeter, which outputs excel files. 

This code was developed for a FRET experiment and has not been thoroughly tested.

Functions
---------
df_from_xls(file):
    Construct a dataframe from an excel file of fluorimeter results.
validate_label_cell(sheet, label_row):
    Check that a given label_row contains an experiment label in column 0.
"""

import xlrd
import pandas as pd


# TODO: add with block that will handle the file opening


def df_from_xls(file):
    """Construct a dataframe from an excel file of fluorimeter results."""
    
    df_list = []

    # assume last sheet (Sheet1) is empty
    for sheet_name in file.sheet_names()[:-1]:
        df = _df_from_sheet(file.sheet_by_name(sheet_name))
        df["Run"] = int(sheet_name[5:])
        df_list.append(df)

    return pd.concat(df_list, ignore_index=True)


def _df_from_sheet(sheet):
    """Construct a dataframe from a single sheet of an excel file.
    
    Construct a dataframe containing parameters, plate location, and values 
    from excel file sheet. If a sheet contains multiple experiments, combine 
    them into one dataframe.
    """

    df_list = []

    for label_row in _find_label_rows(sheet):
        df = _get_measurements(sheet, label_row)

        for key, value in _get_parameters(sheet, label_row).items():
            df[key] = value

        df_list.append(df)

    return pd.concat(df_list, ignore_index=True)


def _find_label_rows(sheet):
    """Search excel file column A for cells containing 'Label'.

    Return a list of zero-indexed rows.
    """

    label_rows = []
    for i in range(sheet.nrows):
        if "Label" in sheet.cell_value(i, 0):
            label_rows.append(i)

    return label_rows


def _get_measurements(sheet, label_row=13):
    """Retrieve fluorescence measurements from plate.

    Return a tidy DataFrame specifying plate row, column, and measured value.
    """

    plate_origin = label_row + 15

    a_dict = {"Plate row": [], "Plate column": [], "Intensity": []}

    # standard 96 well plate has 12 rows and 8 columns
    for row_num in range(1, 13):
        plate_row = sheet.cell_value(plate_origin + row_num, 0)
        if plate_row == "":
            break

        try:
            for col_num in range(1, 9):
                plate_col = sheet.cell_value(plate_origin, col_num)
                if plate_col == "":
                    break

                a_dict["Plate row"].append(plate_row)
                a_dict["Plate column"].append(int(plate_col))
                a_dict["Intensity"].append(
                    sheet.cell_value(plate_origin + row_num, col_num)
                )

        except IndexError:
            pass

    return pd.DataFrame(a_dict)


# default label_row = 13 for the first read
def _get_parameters(sheet, label_row=13):
    """Retrieve paramters from an excel sheet.
    
    Parameters are excitation wavelength, emmission wavelength, and gain. 
    Return a dictionary.
    """

    parameters = {}

    # 2, 3, and 6 are the offsets for ex wavelength, em wavelength, and gain
    for row_add in [2, 3, 6]:
        name = sheet.cell_value(label_row + row_add, 0)
        unit = sheet.cell_value(label_row + row_add, 5)
        value = sheet.cell_value(label_row + row_add, 4)

        if name == "Gain":
            parameters[f"{name}"] = value
        else:
            parameters[f"{name} ({unit})"] = value

    return parameters


def validate_label_cell(sheet, label_row):
    """Check that a given label_row contains an experiment label in column 0.
    
    Raise a RuntimeError if not. Return nothing.
    """

    try:
        assert "Label" in sheet.cell_value(label_row, 0)
    except AssertionError:
        raise RuntimeError(f"Experiment label not found at row {label_row}")
