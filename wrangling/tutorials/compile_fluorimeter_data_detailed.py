"""This is a detailed script to compile data from the Deniz lab fluorimeter.

You can make a shortcut of this file. Double-click the file to run 
it. You will be prompted to enter the path for a folder of .ifx data
files, then for several inputs guiding the program to organize your 
data. Up to three .csv files will be saved in the same folder: 
    "compiled.csv" (the same output as the simple script), 
    "compiled_with_combined_columns.csv", 
    "{variable}_summary.csv" (where variable is a data column you select)
"""

import pandas

from wrangling import fluorimeter, utilities
from wrangling.tutorials import handle_input

# the simple version of the script will be run on import
# including requesting the filepath and saving the compiled file
from compile_fluorimeter_data_simple import (
    filepath,
    df,
    automatically_standardize_concentrations,
)


# this function is useful for requesting multiple columns
def iteratively_request_column_names(
    allowed_list, 
    column_descriptor="Columns selected: ",
    exit_conditions=""
):
    """Query the user for multiple entries from a given list.

    Show the previous inputs with each repeated query.
    
    Return all valid, non-empty inputs in a list. Returned list will include
    non-empty strings in exit_conditions, if given.

    Parameters
    ----------
    allowed_list : list
        the list of columns that may be selected. exit_conditions (default "")
        will also be allowed.
    column_descriptor : str
        printed before each request with a list of columns that have been 
        selected so far. 
    exit_conditions : str or list, default ""
        strings which will cause the termination of the loop. Added to 
        allowed_list and may be included in returned results (except
        empty strings). If exit_conditions = [], after one loop it will be 
        updated to [""]

    """
    if type(exit_conditions) == str:
        exit_conditions = [exit_conditions]

    allowed_list += exit_conditions

    columns = set()
    entry = None
    while entry not in exit_conditions:
        entry = handle_input.interpret(
            f"\n{column_descriptor}{list(columns)}\n",
            handle_input.check_membership,
            list_to_check=allowed_list,
            error_message="That is not a valid column, try again."
        )

        if entry != "":
            columns.add(entry)

        if exit_conditions == []:
            exit_conditions.append("")
            allowed_list += exit_conditions
    
    return list(columns)


# nice formatting for the user
print("\nCOMBINING COLUMNS\n-----------------")

# check if there even are columns that can be combined first
is_any_combined = False
while len(df.columns[df.isna().any()]) >= 2:

    # only print these instructions at the beginning
    print(
        f"\nCurrent columns eligible for combination:\n"
        + str(list(df.columns[df.isna().any()]))
        + "\n\nWhich columns should be combined? "
        + "Type names and hit enter between each, or type 'all'. "
        + "Leave blank to finish or to skip."
    )

    columns_to_combine = iteratively_request_column_names(
        allowed_list=list(df.columns[df.isna().any()]),
        column_descriptor="Columns selected to combine: ",
        exit_conditions=["", "all", "'all'"]
    )

    if "all" in columns_to_combine or "'all'" in columns_to_combine:
        columns_to_combine = df.columns[df.isna().any()]
        print()
    elif len(columns_to_combine) == 1:
        print("Only one column selected. At least two columns needed to combine.")
        # restart asking
        continue
    elif len(columns_to_combine) == 0:
        # if no columns are selected, quit trying to combine.
        break

    # new column name can be anything EXCEPT an existing one or an existing one in brackets
    variable = handle_input.interpret(
        "What should the new combined column be called? ",
        handle_input.exclude_options,
        list_to_exclude=(list(df.columns) + [f"[{x}]" for x in df.columns]),
    )
    
    try:
        df = fluorimeter.break_out_variable(df, columns_to_combine, variable)
        is_any_combined = True
    # if something goes wrong, show the error and repeat the loop
    except RuntimeError as e:
        print("\n" + str(e) + "\n")

df = automatically_standardize_concentrations(df)

# only save new version if changes were made
if is_any_combined:
    df.to_csv(filepath + "/compiled_with_combined_columns.csv")

# nice formatting for the user
print("\nCREATING SUMMARY TABLE\n----------------------")

print(f"\nCurrent column names: {df.columns}")

# only requesting one column
# TODO: enforce that this column must be coercible to float
variable_to_calculate = handle_input.interpret(
    "\nWhat column should be summarized? Leave blank to skip. ",
    handle_input.check_membership,
    list_to_check=list(df.columns) + [""],
    error_message="That is not a column name, try again.",
)

print()

# only ask for follow up info if first question was not skipped
if variable_to_calculate != "":

    print(
        "What column(s) should vary for the rows? Hit enter between each. "
        + "You must enter at least one. Leave blank to finish."
    )
    # requires at least one entry, so exit_conditions = []
    row_variable = iteratively_request_column_names(
        allowed_list=list(df.columns),
        column_descriptor="Data columns selected as summary row variables: ",
        exit_conditions=[]
    )
    
    print(
        "What column(s) should vary for the columns, if any? "
        + "Hit enter between each. Leave blank to finish or to select none."
    )
    column_variable = iteratively_request_column_names(
        allowed_list=list(df.columns),
        column_descriptor="Data columns selected as summary column variables: "
    )

    if column_variable == []:
        column_variable = None

    fluorimeter.make_prism_data(
        df, variable_to_calculate, column_variable, row_variable
    ).to_csv(filepath + f"/{variable_to_calculate}_summary.csv")

input("\nData compilation complete. Press enter to exit.")
