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
    
    TODO: this function is very finicky about exact formatting
    """
    
    df, descriptor = df_descriptor_tuple
    
    title = descriptor[6:descriptor.find("\n")]
    
    title_attributes = [x.strip().rstrip() for x in title.split(" - ")]
    conditions = {}
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
    
    return pd.concat([df, pd.DataFrame(conditions)], axis=1).fillna(method="ffill", axis="index")


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