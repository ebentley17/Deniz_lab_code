"""Functions for handling data from the Deniz lab fluorimeter.

Functions
---------
ifx_to_dataframe(filepath)
    Read in data from a .ifx file generated by the Deniz lab fluorimeter
add_descriptor_data(df_descriptor_tuple, title_as_column=False)
    Add data from descriptor to DataFrame using ifx_to_dataframe() output.
assemble_ifx_files(file_list, **kwargs):
    Import data from a list of .ifx files.
break_out_variable(df, columns=None, variable="titrant"):
    Simplify dataframes of multiple experiments with different variables.
get_corrections(polarizer, slit):
    Select and construct corrections dict meeting specifications.
correct_df_intensity(df, detect_slit=None, slit=None):
    Correct the intensity values in a dataframe.
make_prism_data(
    df,
    variable_to_calculate,
    column_variable="titrant",
    row_variable="[titrant] (nM)",
):
    Group and summarize data for easy transfer to GraphPad Prism.

Depracated
----------
These functions have been moved to wrangling.utilities :
    concentration_to_nM(df, columns)
    plot_averages(df, x_axis, y_axis, cat=None, p=None, palette=None, **kwargs)
"""

import os
import warnings
import pandas as pd
import numpy as np

from importlib import resources

import wrangling.bokeh_scatter as bokeh_scatter
import wrangling.utilities
from . import corrections


def ifx_to_dataframe(filepath):
    """Read in data from a .ifx file generated by the Deniz lab fluorimeter.

    Return (DataFrame, descriptor)
    """

    with open(filepath, "r") as f:
        descriptor = ""
        line = f.readline()
        while "Columns" not in line:
            descriptor += line
            # not stripping whitespace from multi-line descriptor
            line = f.readline()

        column_names = line[8:].rstrip().split(",")

        # proceed past columns line
        line = f.readline().rstrip()

        # G factor info now included after column names
        while "[Data]" not in line:
            descriptor += line
            line = f.readline()

        # skip "[Data]" line
        line = f.readline().rstrip()

        data = []
        while line != "":
            data.append(line)
            line = f.readline().rstrip()

    not_allowed = ["", "\t"]
    for i, line in enumerate(data):
        data[i] = [x.rstrip() for x in line.split(" ") if x not in not_allowed]

    df = pd.DataFrame.from_records(data, columns=column_names)

    return df, descriptor


def add_descriptor_data(df_descriptor_tuple, title_as_column=False):
    """Add data from descriptor to DataFrame using ifx_to_dataframe() output.

    Expects conditions to be specified as "[concentration] [nM/uM] [molecule]",
    and for different molecule specifications to be separated by " - ".

    Does not recognize 'M' for molar; enter in mM.
    """

    df, descriptor = df_descriptor_tuple
    conditions = {}

    title = descriptor[6 : descriptor.find("\n")]

    if title_as_column == True:
        conditions["title"] = title

    title_attributes = [x.strip().rstrip() for x in title.split(" - ")]
    for attribute in title_attributes:
        divisor = attribute.find("mM")
        if divisor == -1:
            divisor = attribute.find("uM")
            if divisor == -1:
                divisor = attribute.find("nM")
                if divisor == -1:
                    divisor = attribute.find("pM")
                    if divisor == -1:
                        continue

        concentration = attribute[: divisor + 2]
        molecule = attribute[divisor + 3 :]

        conditions[f"[{molecule}]"] = [concentration]

    def find_rest_of_line(string):
        """Given a string, return the remainder of that line of descriptor.

        If the string does not exist in the descriptor, return an empty string.
        """
        string_start = descriptor.find(string)
        if string_start == -1:
            return ""
        string_start += len(string)
        string_end = descriptor[string_start:].find("\n") + string_start
        return descriptor[string_start:string_end]

    conditions["comment"] = find_rest_of_line("Comment=")
    conditions["timestamp"] = find_rest_of_line("Timestamp=")
    conditions["ex wavelength (nm)"] = find_rest_of_line(
        "ExcitationWavelength=type:numeric,unit:nm,fixed:"
    )
    conditions["em wavelength (nm)"] = find_rest_of_line(
        "EmissionWavelength=type:numeric,unit:nm,fixed:"
    )

    final_conditions = {
        key: value for key, value in conditions.items() if value != ""
    }

    return pd.concat(
        [df, pd.DataFrame(final_conditions, index=[0])], axis=1
    ).fillna(method="ffill", axis="index")


def assemble_ifx_files(file_list, **kwargs):
    """Import data from a list of .ifx files.
    
    Perform add_descriptor_data(ifx_to_dataframe(filepath)) on each filepath
    in the list and concatenate the results into a single dataframe. Skip
    files that do not end in .ifx

    Parameters
    ----------
    file_list : list of str
        a list of filepaths
    kwargs : allows title_as_column to be passed to add_descriptor_data()

    Returns
    -------
    a pandas DataFrame
    """

    df_list = []

    for filepath in file_list:
        if filepath[-4:] != ".ifx":
            continue

        df = add_descriptor_data(ifx_to_dataframe(filepath), **kwargs)
        df_list.append(df)

    return pd.concat(df_list, ignore_index=True)


def break_out_variable(df, columns=None, variable="titrant"):
    """Simplify dataframes of multiple experiments with different variables.

    For a given DataFrame and columns of concentration, break the column
    names into a "{variable}" column and combine the column values into a
    "[{variable}]" column.

    Parameters
    ----------
    df : a pandas DataFrame
    columns : list of str, default None
        Columns to be combined. If columns=None, all columns containing NaN 
        values are selected. Among all specified columns, each row should 
        contain no more than one non-NaN value. 
    variable : str, default "titrant"
        The new name for the combined columns. Cannot be a column name that 
        exists, as-is or with brackets added.

    Returns
    -------
    A modified DataFrame

    Raises
    ------
    RuntimeError : if "variable" or "[variable]" is a column name in df
    RuntimeError : if selected columns contain more than one valid entry per row

    Example
    -------
    >>> df.head()
    experiment    [specific DNA]    [nonspecific DNA]
    A             NaN               50 nM
    B             50 nM             NaN
    >>> break_out_variable(
            df, 
            columns=["[specific DNA]", "[nonspecific DNA]"], 
            variable="DNA
        ).head()
    experiment    DNA                [DNA]
    A             specific DNA       50 nM
    B             nonspecific DNA    50 nM

    Exception Example
    -----------------
    >>> df.head()
    index   experiment    [specific DNA]    [nonspecific DNA]   [protein]
    0       A             NaN               50 nM               10 nM
    1       B             50 nM             NaN                 NaN
    >>> # columns=None will select all columns with NaN values
    >>> break_out_variable(df, columns=None, variable=DNA)
    RuntimeError("More than one valid entry is detected for row 0. Use this 
        function to combine columns when each row has only one valid entry 
        between the columns.")
    """

    # don't modify in place
    df = df.copy()

    if columns is None:
        columns = df.columns[df.isna().any()]
    
    if len(columns) < 2:
        raise RuntimeError("Fewer than two columns were specified.")

    try:
        assert variable not in df.columns
        assert f"[{variable}]" not in df.columns
    except AssertionError:
        raise RuntimeError(
            "'variable' cannot be a column name that exists, as-is or with brackets added."
        )

    df[variable] = ""
    df[f"[{variable}]"] = np.nan

    for i, row in df.iterrows():
        try:
            # allow no valid entries so you can leave out a titrant column
            assert row[columns].notna().sum() <= 1
        except AssertionError:
            raise RuntimeError(
                f"More than one valid entry is detected for row {i}. "
                + "Use this function to combine columns when each row has "
                + "only one valid entry between the columns."
            )

        for colname in columns:
            if type(row[colname]) is float:
                if np.isnan(row[colname]):
                    continue

            try:
                df.loc[i, variable] = colname.replace("[", "").replace("]", "")
            except:
                df.loc[i, variable] = colname
            df.loc[i, f"[{variable}]"] = row[colname]

    df = df.drop(columns=columns)
    return df


def _construct_corrections_dict(file):
    """Construct a dictionary of corrections.
    
    Given the name of a .ifa corrections file, construct a dictionary
    where the keys are wavelengths (represented as integers) and the values
    are measures of the instrument sensitivity (represented as floats).

    Intensity data should be divided by the correction value corresponding
    to the wavelength at which it was collected.
    """

    str_file = resources.read_text(wrangling.fluorimeter.corrections, file)
    data = str_file[str_file.find("[Data]") + 6 :]
    data = [x for x in data.split("\n") if x != ""]
    corrections = {}
    for entry in data:
        wavelength, correction = [
            x.strip() for x in entry.split("\t") if x != ""
        ]
        corrections.update({int(wavelength[:-3]) : float(correction)})

    return corrections

def _calculate_missing_corrections(corrections_dict):
    """Fill in odd wavelength values in corrections dictionary.
    
    ISS provides corrections for even wavelengths (i.e. 250 nm, 252 nm,
    etc.) For a given dictionary of corrections compiled by
    _construct_corrections_dict(), this function calculates corrections for odd
    wavelengths by averaging the adjacent two values.

    Return a dictionary with integer wavelengths as keys and corrections
    as values.

    Intensity data should be divided by the correction value corresponding
    to the wavelength at which it was collected.
    """

    expanded_dict = {}

    for i in range(250, 901):
        if i in corrections_dict.keys():
            expanded_dict.update({i: corrections_dict[i]})
        else:
            expanded_dict.update(
                {i: (corrections_dict[i - 1] + corrections_dict[i + 1]) / 2}
            )

    return expanded_dict


def get_corrections(polarizer, slit):
    """Select and return corrections dict meeting specifications.
    
    Given the filepath for the folder containing .ifa corrections files
    and the polarization and slit specifications of the experiment, select
    and return the appropriate corrections.

    Intensity data should be divided by the correction value corresponding
    to the wavelength at which it was collected.

    Parameters
    ----------
    polarizer : str
        Must be one of ["horizontal", "vertical", "none"]
    slit : int or float
        Must be one of [0.5, 1, 2]

    Returns
    -------
    Dictionary with integer wavelengths as keys and corrections as values.
    """

    file_lookup_dict = {
        ("horizontal", 0.5): "horizontal polarizer and slit 05.ifa",
        ("horizontal", 1): "horizontal polarizer and slit 1.ifa",
        ("horizontal", 2): "horizontal polarizer and slit 2.ifa",
        ("vertical", 0.5): "vertical polarizer and slit 05.ifa",
        ("vertical", 1): "vertical polarizer and slit 1.ifa",
        ("vertical", 2): "vertical polarizer and slit 2.ifa",
        ("none", 0.5): "without polarizer and slit 05.ifa",
        ("none", 1): "without polarizer and slit 1.ifa",
        ("none", 2): "without polarizer and slit 2.ifa",
    }

    if polarizer is None:
        polarizer = "none"

    try:
        selected_file = (file_lookup_dict[(polarizer.lower(), float(slit))])
    except KeyError:
        raise RuntimeError(
            "polarizer must be one of ['horizontal', 'vertical', 'none']. "
            + "slit must be one of [0.5, 1, 2]."
        )

    return _calculate_missing_corrections(
        _construct_corrections_dict(selected_file)
    )


def correct_df_intensity(df, detect_slit=True, slit=None):
    """Correct the intensity values in a dataframe.
    
    Data is assumed to have been measured without polarizers in place.

    Parameters
    ----------
    df : a pandas DataFrame with an "Intensity" column and an emission wavelength
        column titled either "em wavelength (nm)" or "EmissionWavelength".
        Construct an appropriate df using assemble_ifx_files.
    detect_slit : bool, default True
        Determines if the appropriate slit will be detected from the "comment"
        column of the dataframe. Overwritten by slit if provided
    slit : one of [0.5, 1, 2, or None], default None
        Slit to be passed to get_corrections. Overwrites detect_slit if provided.

    Returns
    -------
    A corrected dataframe.

    Raises
    -----
    RuntimeError if detect_slit and slit are both None
    RuntimeError if detect_slit=True but "comment" column cannot be interpreted.

    Notes
    -----
    If detect_slit=True, expected values for the "comment" column are one of [
        "0.5, 0.5, 0.5, 0.5", 
        "1, 1, 1, 1",
        "2, 2, 2, 2", 
        "0.5 all", 
        "1 all", 
        "2 all"
    ]
    Mixed slits are not supported.
    """

    if slit is not None:
        detect_slit = False
        if slit not in [0.5, 1, 2]:
            raise RuntimeError("slit must be one of [0.5, 1, 2]")

    df = df.copy().astype({"Intensity": float}).reset_index(drop=True)

    corrected_dfs = []
    df["Corrected Intensity"] = np.nan
    for comment, data in df.groupby("comment"):

        if detect_slit:
            if comment in ["2, 2, 2, 2", "2,2,2,2", "2 all"]:
                slit = 2
            elif comment in ["1, 1, 1, 1", "1,1,1,1", "1 all"]:
                slit = 1
            elif comment in ["0.5, 0.5, 0.5, 0.5", "0.5,0.5,0.5,0.5", "0.5 all"]:
                slit = 0.5
            else:
                raise RuntimeError(
                    f"'comment' column contents {comment} could not be interpreted."
                )

        # should be impossible to fail this assertion
        assert slit in [0.5, 1, 2]

        corrections_dict = get_corrections(polarizer="none", slit=slit)

        for i, row in data.iterrows():
            try:
                wavelength = float(row["EmissionWavelength"])
            except (KeyError, ValueError):
                wavelength = float(row["em wavelength (nm)"])

            data.loc[i, "Corrected Intensity"] = row["Intensity"] / corrections_dict[wavelength]

        corrected_dfs.append(data)

    return pd.concat(corrected_dfs)


def make_prism_data(
    df,
    variable_to_calculate,
    column_variable="titrant",
    row_variable="[titrant] (nM)",
    **kwargs,
):
    """Group and summarize data for easy transfer to GraphPad Prism.

    Returns the mean, standard deviation, and count (N) for each grouped entry.

    Parameters
    ----------
    df : a pandas DataFrame
    variable_to_calculate : str
        a column name of the variable to be summarized, often "Intensity" or 
        "Anisotropy". Column must be coercible to float.
    column_variable : str, default "titrant"
        the column name used to group the columns of the summary dataframe
    row_variable : str, default "[titrant] (nM)"
        the column name used to group th rows of the summary dataframe
    kwargs : allow deprecated kwarg names "groupby_variable" and "index_variable"

    Returns
    -------
    a summary DataFrame

    Raises
    ------
    RuntimeError : if df[variable_to_calculate] is not coercible to float    
    """

    # allow deprecated kwarg names
    if "groupby_variable" in kwargs:
        column_variable = kwargs["groupby_variable"]
    if "index_variable" in kwargs:
        row_variable = kwargs["index_variable"]

    for colname in df:
        try:
            df = df.astype({colname: float})
        except ValueError:
            continue

    try:
        assert df[variable_to_calculate].dtype == float
    except AssertionError:
        raise RuntimeError(
            f"Could not coerce column '{variable_to_calculate}' to float. "
            + "This function is intended for quantitative data."
        )

    # force row_variable to be a list
    # column_variable can be string or list because groupby can handle either
    if type(row_variable) == str:
        row_variable = [row_variable]

    if column_variable is None:
        # no column grouping; just grab the variables that are specified
        select = df[[variable_to_calculate] + row_variable]
        return select.groupby(row_variable)[variable_to_calculate].describe()[
            ["mean", "std", "count"]
        ]

    df_list = []

    for col_var, data in df.groupby(column_variable):
        cols_to_report = data[[variable_to_calculate] + row_variable]
        grouped = cols_to_report.groupby(row_variable)[variable_to_calculate].describe()
        select = grouped[["mean", "std", "count"]].transpose()
        multiindex = pd.MultiIndex.from_product(
            [[col_var], ["mean", "std", "count"]], 
            names=[str(column_variable), "value"]
        )
        df_list.append(select.set_index(multiindex))

    return pd.concat(df_list).transpose()


def concentration_to_nM(df, columns):
    """Moved to wrangling.utilities."""

    warnings.warn(
        "This function moved to wrangling.utilities.py", DeprecationWarning
    )
    return wrangling.utilities.concentration_to_nM(df, columns)


def plot_averages(
    df,
    x_axis,
    y_axis,
    cat=None,
    p=None,
    palette=None,
    **kwargs,
):
    """Moved to wrangling.utilities."""

    warnings.warn(
        "This function moved to wrangling.utilities.py", DeprecationWarning
    )
    return wrangling.utilities.plot_averages(
        df, x_axis, y_axis, cat, p, palette, **kwargs
    )
