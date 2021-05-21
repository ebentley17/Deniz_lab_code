import numpy as np
import pandas as pd
import glob
import pytest

import hypothesis
import hypothesis.strategies as st
from hypothesis import given
from hypothesis.extra.pandas import data_frames, column, columns

import wrangling.nanodrop as nd


@given(data_frames(columns=[column("1 (nm)", dtype=int), column("1 (Abs)", dtype=float)]))
def test_with_hypothesis_rename_abs_column_by_wavelength(df):    
    renamed = nd.rename_abs_columns_by_wavelength(df)
    
    if len(df) == 0:
        assert renamed == None
        
    else: 
        assert "1 (nm)" not in renamed.columns
        assert "1 (Abs)" not in renamed.columns
        assert len(renamed) == len(df)
       
        for wavelength in df["1 (nm)"].unique():
            assert f"Abs {int(wavelength)}" in renamed.columns
    
        for row_index, row in df.iterrows():
            original_value = row["1 (Abs)"]
            moved_value = renamed.loc[row_index, f"Abs {int(row['1 (nm)'])}"]
            
            if np.isnan(original_value):
                assert np.isnan(moved_value) == True
            else: 
                assert original_value == moved_value