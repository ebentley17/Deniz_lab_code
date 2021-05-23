"""A script to process nanodrop data.

This script is adapted from the Jupyter notebook of the same name. While it is
more streamlined to use, it is also less forgiving (i.e. you will have to 
rerun the script from the beginning if you make any errors).

Plotting functions are absent from the script.
"""

import re
import warnings
import numpy as np
import pandas as pd

from wrangling import nanodrop
from wrangling.tutorials import handle_input

# Select your files
file_list, file_ext = handle_input.interpret(
    "Type the filepath here:",
    handle_input.validate_file_input
)
    
print(f"\nYou have selected these files:")

# automatically detect the file type
for file_name in file_list:
    slash_index = file_name.rfind("/")
    if slash_index == -1:
        slash_index = file_name.rfind("\\")
    if slash_index == -1:
        print(file_name)
    else:
        print(file_name[slash_index:])
    
if file_ext in ["tsv", "csv"]:
    print(f"\nAutomatically detected file type: {file_ext}")
else:
    file_ext = handle_input.interpret(
        "\nWhat file type are you using? Choose csv or tsv:",
        handle_input.check_membership,
        list_to_check=["tsv", "csv"]
    )

if "tsv" == file_ext:
    file_reader_kwargs=dict(sep="\t")
elif "csv" == file_ext:
    file_reader_kwargs=dict()

"""
Describe your data: Example
---------------------------
I always name my samples in the format: 

[Peptide]_[Peptide Concentration (uM)]_[RNA/Peptide Ratio]

At the nanodrop, I might type: `Peptide1_150_0.5`

I would fill out this section as follows:

    How many pieces of data are in your sample names? 3
    What separator is used in your sample names? _
    Name of data in position 1: Peptide
    Name of data in position 2: Peptide Concentration (uM)
    Name of data in position 3: RNA/Peptide Ratio
"""
# Describe your sample names:
args, kwargs = handle_input.request_parsekey_specifications()
MyKey = nanodrop.ParseKey(*args, **kwargs)

print(
    f"\nYour sample names take the form: "
    + f"[{f']{MyKey.separator}['.join(MyKey.column_names)}]"
)

# Decide how to handle unusual cases
# If you keep these samples, they will appear in your dataframe, 
# but no information will be extracted from their names. 

drop_buffers = handle_input.interpret(
    "Should samples labeled as buffer or blank be dropped?",
    handle_input.yes_no_to_bool,
)

drop_incorrectly_named_samples = handle_input.interpret(
    "Should incorrectly named samples be dropped?",
    handle_input.yes_no_to_bool,
)

# ## Reformat the data
# This may take several seconds, especially if you have a lot of files

data = nanodrop.tidy_data(
    file_list, 
    file_reader_kwargs=file_reader_kwargs,
    ParseKey=MyKey,
    drop_incorrectly_named_samples=drop_incorrectly_named_samples,
    drop_buffers=drop_buffers
)

# show output
print(data)

# Saving your data 
new_file_name = handle_input.interpret(
    "What would you like to name the file? "
    + "Please enter the full path."
)
if new_file_name[-4:] != ".csv":
    new_file_name += ".csv"

data.to_csv(new_file_name, index=False, float_format="%.3f")

"""
Troubleshooting
--------------- 
- the file is empty or has fewer rows than I expected
    You probably described your data incorrectly and told the 
    program to drop incorrectly named samples. The most common 
    problem is incorrectly entering the separator or number of
    data chunks. Try re-entering your data description. Otherwise, 
    your naming scheme may be inconsistent.
- the file has a lot of empty columns
    You may described your data incorrectly and told the notebook 
    to keep incorrectly named samples, or you may have kept a large 
    number of buffer measurements. If the program is unable to parse 
    your sample names, it cannot fill columns. The most common 
    problem is incorrectly entering the separator or number of data 
    chunks. Try re-entering your data description. Otherwise, your 
    naming scheme may be inconsistent.
- found a bug that isn't mentioned here?
    Send me an email at ebentley@scripps.edu.
"""