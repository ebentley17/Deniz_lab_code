"""Useful code for wrangling data from many instrument types."""

import pandas as pd
import bokeh.plotting

import wrangling.bokeh_scatter as bokeh_scatter


def break_out_date_and_time(df, breakout_column="Date and Time", date_time_split=" "):
    """
    Breaks a specified column into separate "Date" and "Time" columns.
    Deletes the original column.
    Returns the modified dataframe.
    
    Expects date_time_split to appear for the first time between the "date" and "time" entries.
    Any following splits will be grouped with "time".
    """

    df["Date"] = ""
    df["Time"] = ""

    for i, _ in df.iterrows():
        # specify one split to keep AM/PM with time
        date_and_time_list = df[breakout_column][i].split(date_time_split, 1)
        date, time = tuple(date_and_time_list)
        df.loc[i, "Date"] = date
        df.loc[i, "Time"] = time

    df = df.drop([breakout_column], axis=1)

    return df


def drop_zeros(df, columns):
    """
    Drops rows that contain zeros in the specified column(s) to allow log scale plotting.
    Converts specified column(s) to floats.
    
    Parameters
    ----------
    df: a pandas DataFrame
    columns: str or list-like
        column name(s) from which to drop zeros
        
    Returns
    -------
    An equivalent pandas DataFrame, minus rows that contained zeros in the specified column(s).
    """

    if type(columns) == str:
        columns = [columns]

    for column in columns:
        df = df.astype({column: float})
        zeros = df.loc[df[column] == 0, :]
        df = df.drop(axis=0, index=zeros.index).reset_index(drop=True)

    return df


# TODO: allow selection of what unit to convert to
def concentration_to_nM(df, columns):
    """For a given DataFrame and column, converts uM and pM concentration values to nM.
    Renames the column to include (nM).
    """
    
    if type(columns) == str:
        columns = [columns]
        
    for column in columns:
        for i, row in df.iterrows():
            molar_index = row[column].find("M")
            value = float(row[column][:molar_index-1])
            if "uM" in row[column]:
                df.loc[i, column] = value*1000
            elif "pM" in row[column]:
                df.loc[i, column] = value/1000
            else:
                df.loc[i, column] = value
    
    df = df.rename(columns={column : f"{column} (nM)" for column in columns})
    
    return df


def find_outlier_bounds(df, col_to_check, groupby=None):
    """
    Calculate upper and lower outlier bounds.
    Outliers are defined as data points 1.5x the interquartile range 
        for all other data with matching ParseKey parameters, 
        NOT for the total dataset.
    
    Parameters
    ----------
    df : a pandas DataFrame
    col_to_check : str
        the name of a column in df in which to check for outliers 
    groupby : str or list, optional
        a column name or list of column names by which to group df before calculating outliers separately
        
    Returns
    -------
    a tuple (lower_outlier_bound, upper_outlier_bound)
    where each position contains a pandas Series
    indexed by groupby column(s) if provided (multiple columns will result in a multiindex)
    """
    
    if groupby == None:
        grouped = df
    else:    
        grouped = df.groupby(groupby)

    percentile_75 = grouped[col_to_check].quantile(.75)
    percentile_25 = grouped[col_to_check].quantile(.25)
    
    interquartile_range = percentile_75 - percentile_25
    lower_outlier_bound = percentile_25 - 1.5 * interquartile_range
    upper_outlier_bound = percentile_75 + 1.5 * interquartile_range
    
    return lower_outlier_bound, upper_outlier_bound


def identify_outliers(df, col_to_check, **kwargs):
    """
    Identifies outliers among measurements in given column of a dataframe.
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

    outlier_bounds = pd.DataFrame(data=
                                  {"lower": lower,
                                  "upper": upper}
                                 ).reset_index()

    df_with_bounds = pd.merge(df, outlier_bounds)
    outliers = df_with_bounds.loc[(df_with_bounds[col_to_check] > df_with_bounds["upper"]) |
                                  (df_with_bounds[col_to_check] < df_with_bounds["lower"])
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
    palette=bokeh_scatter.scatter_palette,
    **kwargs
):
    """Add lines defining averages of y_axis values at each point along x_axis to an existing plot.
    Separate lines are created for each cat variable.
    
    Parameters
    ----------
    df : pandas DataFrame
    x_axis : str
        column in df; can be numerical or categorical
    y_axis : str
        numerical column in df
    cat : str
        column in df to distinguish categories; treated as categorical
    palette : list-like
        colors to make lines; default matches palette from bokeh_scatter.py
    p : bokeh.plotting.Figure instance, or None (default)
        if p=None, a new plot will be created
    **kwargs : kwargs to pass to bokeh.plotting.Figure() 
        only used if p=None
    """
    
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


# TODO: normalize data
# TODO: plotting, maybe
# TODO: export