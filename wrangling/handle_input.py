"""Functions to interpret user input in "Guide for Non-Coders.ipynb" 
to simplify useage of wrangling.nanodrop.tidy_data()
"""

import sys
import warnings
import glob
import numpy as np

clean_legend_locations = ['top left', 'top center', 'top right', 
                          'center left', 'center', 'center right', 
                          'bottom left', 'bottom center', 'bottom right'] 
allowed_legend_locations = clean_legend_locations + [x.replace(" ", "_") for x in clean_legend_locations] + ["", "None"]


def interpret(instructions, input_manipulator=lambda a : a, error_message=None, **kwargs):
    """A while loop to repeat a request until the input matches an allowed one.
    Accepts "quit" as an input and returns None.
    
    Parameters
    ----------
    instructions : str
        provided at the input request
    input_manipulator : function; default returns input unchanged
        takes user input as its only arg
        changes user input and throws an error at invalid inputs
    error_message : str, default None
        to display if the user gives an incorrect input
        only provide for very simple input_manipulator functions; otherwise you may mask important errors
    **kwargs : to be passed to input_manipulator
    """
    
    is_valid_input = False    
    while not is_valid_input:
        user_input = input(instructions)
        if user_input.lower() == "quit":
            sys.exit()
        
        try:
            user_input = input_manipulator(user_input, **kwargs)
            is_valid_input = True
        except Exception as e:
            if error_message is None:
                print(e)
            else:
                print(error_message)
    
    return user_input


def evaluate_kwargs_at_input(user_input, **kwargs):
    """Checks whether kwargs are functions, then attempts to evaluate them at user_input.
    Returns the full list of kwargs with functions evaluated.
    If errors are encountered, returns the unevaluated function.
    """
    
    for kwarg_name, kwarg_value in kwargs.items():
        if str(type(kwarg_value)) == "<class 'function'>":
            try:
                kwargs[kwarg_name]=kwarg_value(user_input)
            except:
                pass
            
    return kwargs


def confirm(confirm_message="Are you sure?"):
    """Asks the user for confirmation. Raises an error with no message if user responds "no". Returns nothing."""
    
    is_proceed = interpret(
        confirm_message,
        yes_no_to_bool
    )
    
    if not is_proceed:
            raise RuntimeError

            
def file_or_folder(file_name):
    """Checks if a glob-able file name is a file or folder. Returns "file" or "folder" as a string.
    A pathname that doesn't result in a valid file with glob returns None.
    Takes only one file at a time!
    """
   
    if len(glob.glob(file_name)) == 0:
        return
    elif len(glob.glob(file_name)) != 1:
        raise RuntimeError("Too many files provided.")
        
    elif file_name[-1] == "/" or file_name[-1] == "\\":
        return "folder"
    else:
        if len(glob.glob(file_name+"/")) == 1:
            return "folder"
        else:
            return "file"

            
def validate_file_input(string):
    """Takes a specification of files as a string and returns a tuple (list, str), where
        index 0 is a list of specific file paths,
        index 1 is the detected file extension, or None if the files don't have extensions
    
    Requires at least one file to be specified; requires files with extensions to have the same one.
    Optionally allows files without extensions.
    Throws an error if those requirements aren't met.
    """
    
    file_folder_dict = {file_name : file_or_folder(file_name) for file_name in glob.glob(string)}
    
    while "folder" in file_folder_dict.values():
        folder_list = [file_name for file_name, is_file_or_folder in file_folder_dict.items()
                       if is_file_or_folder == "folder"]
        
        ignore_or_include = interpret(
            f"This filepath includes the following folder(s): {folder_list}" 
            + "\nWould you like to 'ignore' or 'include' folder contents?",
            check_membership,
            list_to_check=["ignore", "include"]
        )
        
        for folder_name in folder_list:
            del file_folder_dict[folder_name]
                
            if ignore_or_include == "include":
                if folder_name[-1] != "/" and folder_name[-1] != "\\":
                    folder_name += "/"
                folder_name += "*"
                
                file_folder_dict.update({file_name : file_or_folder(file_name) 
                                         for file_name in glob.glob(folder_name)})
    
    if len(file_folder_dict) == 0:
        raise RuntimeError("No files were specified.")
    
    # only check for matching extensions on files that HAVE extensions
    files_with_ext = [file_name for file_name in file_folder_dict.keys() if "." in file_name]
    
    if len(files_with_ext) < len(file_folder_dict):
        confirm("Some files do not have a file extension. They may not all be the same type, which would cause problems."
        + "\nDo you want to proceed anyway?")

    if len(files_with_ext) == 0:
        return list(file_folder_dict.keys()), None
    
    check_ext = files_with_ext[0][files_with_ext[0].rfind(".")+1:]
    do_files_match = True
    for file_name in files_with_ext:          
        file_ext = file_name[file_name.rfind(".")+1:]
        if file_ext != check_ext:
            do_files_match = False
            break
    
    if not do_files_match:
        confirm("Files have different file extensions. Mixing file types will cause problems."
                + "\nDo you want to proceed anyway?")
        check_ext = None
    
    return list(file_folder_dict.keys()), check_ext


def check_positive_int(string):
    """Converts a string to integer and checks if it's positive. Raises an error if not. Returns the int."""
    
    if int(string) > 0:
        return int(string)
    else:
        raise RuntimeError("Integer must be positive.")


def string_to_type(string):
    """Useful for converting user input to types passable to ParseKey.
    Accepts str, int, float, or bool.
    """
    if string.lower() in ["string", "str"]:
        data_type = str
    elif string.lower() in ["float", "number", "decimal"]:
        data_type = float
    elif string.lower() in ["integer", "int"]:
        data_type = int
    elif string.lower() in ["boolean", "bool"]:
        data_type = bool
    else:
        raise RuntimeError("Invalid input. Enter a type str, int, float, or bool.")
    
    return data_type


def yes_no_to_bool(string):
    """Converts 'yes' or 'no' inputs to True or False booelan. Throws an error at other inputs."""

    if string.lower() in ["yes", "y"]:
        return True
    elif string.lower() in ["no", "n"]:
        return False
    else:
        raise RuntimeError("Invalid input. Enter yes or no.")
        

def check_membership(string, list_to_check, is_confirm=None, **kwargs):
    """Checks if input is in a given list. Returns the input if yes; raises an error if not. Case sensitive.
    
    Parameters
    ----------
    string : str
        usually input provided by another function
    list_to_check : list-like
        collection of items to check whether string is in
    is_confirm : bool, default None
        determines whether to ask for confirmation
        if None, defer to is_confirm_function; treated as False if not provided
        when provided, overrides is_confirm_function
        
    optional kwargs: if functions are provided, they will be evaluated at "string"
    
    is_confirm_function : function that evaluates to bool, default None
        treated as False if an error is thrown
        not used if is_confirm is explicitly provided
    confirm_message : str, or function to be evaluated at "string" and return str
        to be passed to confirm()
    """
    
    try:
        assert string in list_to_check
    except AssertionError:
        raise RuntimeError(f"Input must be one of {list_to_check}.")
    
    kwargs = evaluate_kwargs_at_input(string, **kwargs)
    
    if is_confirm is None:
        try:
            is_confirm = kwargs.pop("is_confirm_function")
        except:
            is_confirm=False        
        
    if is_confirm == True:
        confirm(**kwargs) 
         
    return string


def exclude_options(string, list_to_exclude):
    """Checks to make sure input is not in a given list. 
    Returns the input if yes; raises an error if not. 
    Case sensitive.
    """
    try:
        assert string not in list_to_exclude
    except AssertionError:
        raise RuntimeError(f"Input may not be one of {list_to_exclude}.")
    
    return string


def request_parsekey_specifications():
    """Queries the user for args to pass to ParseKey."""
    
    number_of_pieces = interpret(
        "How many pieces of data are in your sample names?",
        check_positive_int,
        "You must enter a positive integer."
    )

    if number_of_pieces > 1:
        # use interpret function instead of input() to allow universal "quit" exiting
        separator = interpret("What separator is used in your sample names?")
    else:
        separator = None

    names = []    
    for i in range(number_of_pieces):
        name = interpret(
            f"Name of data in position {i+1}:", 
            exclude_options,
            f"You cannot repeat column names. Previous names: {names}",
            list_to_exclude=names
        ) 
        names.append(name)
    args = [(name, str) for name in names]
    
    return args, {"separator" : separator}


def request_plot_specifications(data):
    """Queries the user for kwargs to pass to bokeh_scatter.scatter(). Can be passed directly.
    Cleans up provided x, y columns of data by dropping NAs, dropping empty strings, and converting to float.
    """
    
    kwargs = {}
    
    kwargs["x"] = interpret(
        "What column should be plotted on the x axis?",
        check_membership,
        f"Choose one of {data.columns.values} (omit quotation marks)",
        list_to_check=data.columns.values,
    )

    is_x_log = interpret(
        "Should the x axis be a log scale?", yes_no_to_bool,
    )

    if is_x_log:
        kwargs["x_axis_type"] = "log"

    kwargs["y"] = interpret(
        "What column should be plotted on the y axis?",
        check_membership,
        f"Choose one of {data.columns.values} (omit quotation marks)",
        list_to_check=data.columns.values,
    )

    is_y_log = interpret(
        "Should the y axis be a log scale?", yes_no_to_bool,
    )

    if is_y_log:
        kwargs["y_axis_type"] = "log"

    cat = interpret(
        "What column should determine the color of points, if any?",
        check_membership,
        f"Choose one of {data.columns.values} (omit quotation marks), or leave blank",
        # these kwargs to be passed to check_membership
        list_to_check=np.append(data.columns.values, ["", "None"]),
        is_confirm_function=lambda a: len(data[a].unique()) > 10,
        confirm_message=lambda a: f"This column will result in {len(data[a].unique())} colors."
        + "\nOnly 10 different colors are available by default. Over 100 colors will slow down execution."
        + "\nAre you sure you want to proceed?",
    )

    if cat not in ["", "None"]:
        kwargs["cat"] = cat

    title = interpret("What would you like to title the plot, if anything?")
    
    if title not in ["", "None"]:
        kwargs["title"] = title
    
    # catch a FutureWarning that results from comparing non-string columns to ""
    with warnings.catch_warnings():
        warnings.simplefilter(action='ignore', category=FutureWarning)
    
        kwargs["data"] = data.dropna(axis="index", subset=[kwargs["x"], kwargs["y"]]
                            ).drop(index=data.loc[(data[kwargs["x"]] == "") | (data[kwargs["y"]] == "")].index
                            ).astype({kwargs["x"]: float, kwargs["y"]: float})
    
    return kwargs