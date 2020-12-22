"""Functions for handling data from the Deniz lab fluorimeter."""

import os
import warnings
import pandas as pd

import wrangling.bokeh_scatter as bokeh_scatter
import wrangling.utilities


def ifx_to_dataframe(filepath):
    """Reads in data from the Deniz lab fluorimeter .ifx files.
    
    Returns (DataFrame, descriptor)
    """
    
    with open(filepath, 'r') as f:
        descriptor = ""
        line = f.readline()
        while "Columns" not in line:
            descriptor += line
            #not stripping whitespace from multi-line descriptor
            line = f.readline()

        column_names = line[8:].rstrip().split(",")

        # proceed past columns line
        line = f.readline().rstrip()

        # G factor info now included after column names
        while "[Data]" not in line:
            descriptor += line
            line = f.readline()

        #skip "[Data]" line
        line = f.readline().rstrip()

        data = []
        while line != '':
            data.append(line)
            line = f.readline().rstrip()        

    not_allowed = ["", "\t"]
    for i, line in enumerate(data):
        data[i] = [x.rstrip() for x in line.split(" ") if x not in not_allowed]
        
    df = pd.DataFrame.from_records(data, columns=column_names)
    
    return df, descriptor


def add_descriptor_data(df_descriptor_tuple):
    """Given a DataFrame and descriptor from a .idx file, 
    returns a DataFrame with info from the descriptor concatenated as new columns.
    
    Expects conditions to be specified as "[concentration] [nM/uM] [molecule]", 
    and for different molecule specifications to be separated by " - "
    """
    
    df, descriptor = df_descriptor_tuple
    conditions = {}
    
    title = descriptor[6:descriptor.find("\n")]
    title_attributes = [x.strip().rstrip() for x in title.split(" - ")]
    for attribute in title_attributes:
        divisor = attribute.find("uM")
        if divisor == -1:
            divisor = attribute.find("nM")
            if divisor == -1:
                divisor = attribute.find("pM")
                if divisor == -1:
                    continue
      
        concentration = attribute[:divisor+2]
        molecule = attribute[divisor+3:]
        
        conditions[f"[{molecule}]"] = [concentration]

    def find_rest_of_line(string):
        """Given a string that exists in descriptor, returns the remainder of that line of descriptor."""
        string_start = descriptor.find(string) + len(string)
        string_end = descriptor[string_start : ].find("\n") + string_start
        return descriptor[string_start : string_end]

    conditions["comment"] = find_rest_of_line("Comment=")
    conditions["timestamp"] = find_rest_of_line("Timestamp=")
    conditions["ex wavelength (nm)"] = find_rest_of_line("ExcitationWavelength=type:numeric,unit:nm,fixed:")
    conditions["em wavelength (nm)"] = find_rest_of_line("EmissionWavelength=type:numeric,unit:nm,fixed:")
    
    return pd.concat([df, pd.DataFrame(conditions, index=[0])], axis=1).fillna(method="ffill", axis="index")


def assemble_ifx_files(file_list):
    """Performs add_descriptor_data(ifx_to_dataframe(filepath)) on each filepath in the list
    and concatenates the results into a single dataframe.
    """
    df_list = []

    for filepath in file_list:
        df = add_descriptor_data(ifx_to_dataframe(filepath))
        df_list.append(df)

    return pd.concat(df_list, ignore_index=True)


def break_out_variable(df, columns=None, variable="titrant"):
    """This is used to simplify dataframes of multiple experiments with different variables.
    For a given DataFrame and columns of concentration, 
    breaks the column names into a "{variable}" column 
    and combines the column values into a "[{variable}]" column.
    
    If no columns are provided, all columns with NaN values are assumed
    to be variable entries. This only works if there is only one variable.
    
    Only one kind of variable may be addressed at once.
    """
    
    if columns is None:
        columns = df.columns[df.isna().any()]
    
    df[variable] = ""
    df[f"[{variable}]"] = ""
    
    for i, row in df.iterrows():
        try:
            assert row[columns].notna().sum() == 1
        except AssertionError:
            raise RuntimeError(
                f"More than one valid entry is detected for row {i}. " +
                "Use this function to combine columns when each row has " +
                "only one valid entry between the columns."
            )
            
        for colname in columns:
            if type(row[colname]) is str:
                df.loc[i, variable] = colname.replace("[", "").replace("]", "")
                df.loc[i, f"[{variable}]"] = row[colname]
                
    df = df.drop(columns=columns)
    return df


def make_prism_data(
    df, 
    groupby_variable="titrant",
    index_variable="[titrant] (nM)",
    variable_to_calculate="Anisotropy"
):
    """Returns the mean, standard deviation, and count for each grouped entry
    for easy copy and paste into prism. All variables should be column names in df.
    """
    
    df_list = []
    
    if groupby_variable is None:
        select = df[[index_variable, variable_to_calculate]].astype(float)
        return select.groupby(index_variable)[variable_to_calculate].describe()[["mean", "std", "count"]]
    
    for titrant, data in df.groupby(groupby_variable):
        floats = data[[variable_to_calculate, index_variable]].astype(float)
        grouped = floats.groupby(index_variable)[variable_to_calculate].describe()
        select = grouped[["mean", "std", "count"]].transpose()
        multiindex = pd.MultiIndex.from_product(
            [[titrant], ["mean", "std", "count"]], names=[groupby_variable, "value"]
        )
        df_list.append(select.set_index(multiindex))

    return pd.concat(df_list).transpose()


def concentration_to_nM(df, columns):
    """Moved to wrangling.utilities."""
    
    warnings.warn("This function moved to wrangling.utilities.py", DeprecationWarning)
    return wrangling.utilities.concentration_to_nM(df, columns)


def plot_averages(
    df, 
    x_axis, 
    y_axis, 
    cat=None, 
    p=None,
    palette=bokeh_scatter.scatter_palette,
    **kwargs
):
    """Moved to wrangling.utilities."""
    
    warnings.warn("This function moved to wrangling.utilities.py", DeprecationWarning)
    return wrangling.utilities.plot_averages(
        df, 
        x_axis, 
        y_axis, 
        cat=None, 
        p=None,
        palette=bokeh_scatter.scatter_palette,
        **kwargs
    )