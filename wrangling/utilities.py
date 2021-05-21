"""Useful code for wrangling data from many instrument types.

Functions
---------
break_out_date_and_time(df, column="Date and Time", split=" ")
    Break a specified column into separate "Date" and "Time" columns.
drop_zeros(df, columns)
    Drop rows that contain zeros in the specified column(s) for log plotting.
standardize_concentration(df, columns, unit="nM")
    Make all concentrations match the given unit.
find_outlier_bounds(df, col_to_check, groupby=None)
    Calculate upper and lower outlier bounds.
identify_outliers(df, col_to_check, **kwargs)
    Identify outliers among measurements in given column of a dataframe.
plot_averages(df, x_axis, y_axis, cat=None, p=None, palette=None, **kwargs)
    Plot average values as lines.

Depracated
----------
concentration_to_nM(df, columns)
    Deprecated. Use standardize_concentration() with the kwarg unit='nM'.
"""

import warnings
import pandas as pd
import numpy as np
import bokeh.plotting

import wrangling.bokeh_scatter as bokeh_scatter


def break_out_date_and_time(
    df, 
    column="Date and Time", 
    split=" ",
    **kwargs
):
    """Break a specified column into separate "Date" and "Time" columns.

    Delete the original column and return the modified dataframe. This function
    expects {split} to appear for the first time between the "date" 
    and "time" entries. Any following splits will be grouped with "time".

    Parameters
    ----------
    df : a pandas DataFrame
    column : str, default "Date and Time"
        column name whose contents should be split
    split : str, default " "
        separates the Date from the Time entries. The first appearance of this 
        string will be used to split the entries and all subsequent appearances 
        will be ignored.
    **kwargs : allows deprecated arg names breakout_column and date_time_split

    Returns
    -------
    A modified dataframe.

    Examples
    --------
    >>> df.head()
    experiment    Date and Time
    A             1/1/2000 12:00 
    B             1/1/2000 12:00:00 PM
    >>> break_out_date_and_time(df, column="Date and Time", split=" ")
    experiment    Date        Time
    A             1/1/2000    12:00 
    B             1/1/2000    12:00:00 PM
    """

    # TODO: allow specification of whether to keep subsequent splits

    # don't modify in place
    df = df.copy()

    if "breakout_column" in kwargs:
        column = kwargs["breakout_column"]
    if "date_time_split" in kwargs:
        split = kwargs["date_time_split"]

    df["Date"] = ""
    df["Time"] = ""

    for i, _ in df.iterrows():
        # specify one split to keep AM/PM with time
        date_and_time_list = df[column][i].split(split, 1)
        date, time = tuple(date_and_time_list)
        df.loc[i, "Date"] = date
        df.loc[i, "Time"] = time

    df = df.drop([column], axis=1)

    return df


def drop_zeros(df, columns):
    """Drop rows that contain zeros in the specified column(s) for log plotting.
    
    Drop zeros and convert specified column(s) to floats.

    Parameters
    ----------
    df: a pandas DataFrame
    columns: str or list-like
        column name(s) from which to drop zeros

    Returns
    -------
    A modified dataframe.
    """

    # don't modify in place
    df = df.copy()

    if type(columns) == str:
        columns = [columns]

    for column in columns:
        df = df.astype({column: float})
        zeros = df.loc[df[column] == 0, :]
        df = df.drop(axis=0, index=zeros.index).reset_index(drop=True)

    return df


# TODO: let columns select all columns with brackets by default
# TODO: allow dictionary of column : unit
def standardize_concentration(df, columns, unit="nM"):
    """Make all concentrations match the given unit.
    
    For a given DataFrame and column, convert mM, uM, nM, and pM concentration 
    values to the specified unit (default nM). Rename the column to include 
    ({unit}).

    Parameters
    ----------
    df : a pandas DataFrame
    columns : str or list
        column name(s) to be converted to the given unit
    unit : one of ["mM", "uM", "nM", "pM"], default "nM"

    Returns
    -------
    A modified dataframe.

    Examples
    --------
    >>> df.head()
    experiment    [DNA]
    A             100 nM 
    B             1 uM 
    >>> standardize_concentration(df, columns="[DNA]", unit="nM").head()
    experiment    [DNA] (nM)
    A             100.0 
    B             1000.0
    """
    
    conversions_dict = {
        "mM to mM": 1,
        "mM to uM": 1000,
        "mM to nM": 1000000,
        "mM to pM": 1000000000,
        "uM to mM": 1 / 1000,
        "uM to uM": 1,
        "uM to nM": 1000,
        "uM to pM": 1000000,
        "nM to mM": 1 / 1000000,
        "nM to uM": 1 / 1000,
        "nM to nM": 1,
        "nM to pM": 1000,
        "pM to mM": 1 / 1000000000,
        "pM to uM": 1 / 1000000,
        "pM to nM": 1 / 1000,
        "pM to pM": 1,
    }

    # don't modify in place
    df = df.copy().reset_index(drop=True)

    if type(columns) == str:
        columns = [columns]

    for column in columns:
        for i, row in df.iterrows():

            # variables that didn't exist in all concatanated dfs will be represented as NaN
            if type(row[column]) is float:
                if np.isnan(row[column]):
                    df.loc[i, column] = 0
                    continue
                else:
                    raise RuntimeError(
                        f"Something has gone wrong in row {i}, column {column}. "
                        + "Value is {row[column]}."
                    )

            molar_index = row[column].find("M")
            current_unit = row[column][molar_index - 1 : molar_index + 1]
            if current_unit not in ["mM", "uM", "nM", "pM"]:
                raise RuntimeError(
                    f"Unit {current_unit} not recognized in row {i}, column {column}."
                )
            value = float(row[column][: molar_index - 1])

            df.loc[i, column] = value * conversions_dict[f"{current_unit} to {unit}"]

    df = df.rename(columns={column: f"{column} ({unit})" for column in columns})

    return df


def find_outlier_bounds(df, col_to_check, groupby=None):
    """Calculate upper and lower outlier bounds.

    Outliers are defined as data points 1.5x the interquartile range
        for all other data with matching ParseKey parameters,
        NOT for the total dataset.

    Parameters
    ----------
    df : a pandas DataFrame
    col_to_check : str
        the name of a column in df in which to check for outliers
    groupby : str or list, optional
        a column name or list of column names by which to group df before 
        calculating outliers separately

    Returns
    -------
    a tuple (lower_outlier_bound, upper_outlier_bound) where each position 
    contains a pandas Series, indexed by groupby column(s) if provided (multiple 
    columns will result in a multiindex)
    """

    if groupby == None:
        grouped = df
    else:
        grouped = df.groupby(groupby)

    percentile_75 = grouped[col_to_check].quantile(0.75)
    percentile_25 = grouped[col_to_check].quantile(0.25)

    interquartile_range = percentile_75 - percentile_25
    lower_outlier_bound = percentile_25 - 1.5 * interquartile_range
    upper_outlier_bound = percentile_75 + 1.5 * interquartile_range

    return lower_outlier_bound, upper_outlier_bound


def identify_outliers(df, col_to_check, **kwargs):
    """Identify outliers among measurements in given column of a dataframe.

    Outliers are defined as data points 1.5x the interquartile range
        for all other data with matching ParseKey parameters,
        NOT for the total dataset.

    Parameters
    ----------
    df : a pandas DataFrame
    col_to_check : str
        the name of a column in df in which to check for outliers
    **kwargs : kwargs to be passed to find_outlier_bounds()

    Returns
    -------
    The same dataframe with a new column "Outliers," containing booleans.
    """

    lower, upper = find_outlier_bounds(df, col_to_check, **kwargs)

    outlier_bounds = pd.DataFrame(
        data={"lower": lower, "upper": upper}
    ).reset_index()

    df_with_bounds = pd.merge(df, outlier_bounds)
    outliers = df_with_bounds.loc[
        (df_with_bounds[col_to_check] > df_with_bounds["upper"])
        | (df_with_bounds[col_to_check] < df_with_bounds["lower"])
    ].index

    df_with_bounds[f"{col_to_check} outlier"] = False
    df_with_bounds.loc[outliers, f"{col_to_check} outlier"] = True

    return df_with_bounds.drop(labels=["lower", "upper"], axis="columns")


def plot_averages(
    df,
    x_axis,
    y_axis,
    cat=None,
    p=None,
    palette=None,
    **kwargs,
):
    """Plot average values as lines.
    
    Plot lines defining averages of y_axis values at each point along x_axis, 
    optionally adding to an existing plot. Separate lines are created for each 
    cat variable.

    Parameters
    ----------
    df : pandas DataFrame
    x_axis : str
        column in df; can be numerical or categorical
    y_axis : str
        numerical column in df
    cat : str
        column in df to distinguish categories; treated as categorical
    palette : list-like, default None
        colors to make lines. If None, uses palette from bokeh_scatter.py
    p : bokeh.plotting.Figure instance, or None (default)
        if p=None, a new plot will be created
    **kwargs : kwargs to pass to bokeh.plotting.Figure()
        only used if p=None
    """

    if palette is None:
        palette = bokeh_scatter.scatter_palette

    if p is None:
        p = bokeh.plotting.Figure(**kwargs)

    df_slice_list = []
    # TODO: make this able to accept a list of cats using groupby
    if cat is not None:
        for cat_item in df[cat].unique():
            df_slice_list.append(df.loc[df[cat] == cat_item])
    else:
        df_slice_list.append(df)

    for i, df_slice in enumerate(df_slice_list):
        averages = df_slice.groupby(x_axis)[y_axis].quantile(0.5)
        x = averages.index.values
        y = averages.values
        p.line(x, y, color=palette[i % len(palette)])

    return p


def concentration_to_nM(df, columns):
    """Deprecated. Use standardize_concentration() with the kwarg unit='nM'."""

    warnings.warn("Use standardize_concentration() instead.", DeprecationWarning)

    return standardize_concentration(df, columns, unit="nM")


# TODO: normalize data
# TODO: plotting, maybe
# TODO: export
