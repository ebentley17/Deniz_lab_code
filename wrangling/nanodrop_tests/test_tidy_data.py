"These tests of the tidy_data() function from nanodrop.py take a few seconds to run."

import numpy as np
import pandas as pd
import glob
import pytest

from importlib import resources

import wrangling.nanodrop as nd


_parent_dir = __file__[:__file__.rfind("\\")]


def test_tidy_data(to_glob=_parent_dir+"/test_data/*.tsv", **kwargs):
    """For testing a variety of input kwargs"""

    file_list = glob.glob(to_glob)
    df = nd.tidy_data(file_list, **kwargs)

    assert (
        df.columns == [
            "Sample ID",
            "Abs 350",
            "Abs 600",
            "Peptide",
            "Peptide concentration (uM)",
            "RNA/Peptide Ratio",
            "Date",
            "Time",
        ]
    ).all()

    float_cols = [
        "Abs 350",
        "Abs 600",
        "Peptide concentration (uM)",
        "RNA/Peptide Ratio",
    ]
    for col in float_cols:
        assert df[col].dtype == float

    return df


def test_run_all_defaults():
    df = test_tidy_data(to_glob=_parent_dir+"/test_data/*.tsv")

    for peptide in df["Peptide"].values:
        assert "RG" in peptide


def test_run_all_read_csv():
    df = test_tidy_data(
        to_glob=_parent_dir+"/test_data/*.csv",
        file_reader_kwargs={},
        drop_incorrectly_named_samples=True,
    )

    for peptide in df["Peptide"].values:
        assert "RG" in peptide


def test_run_all_raise_incorrect_samples_warning():
    with pytest.warns(UserWarning) as sample_name_divergence:
        df = test_tidy_data(
            to_glob=_parent_dir+"/test_data/*.csv",
            file_reader_kwargs={},
            drop_incorrectly_named_samples=False,
        )
    assert (
        "Identify incorrectly named samples by running analyze_sample_names on your DataFrame."
        in sample_name_divergence[0].message.args[0]
    )

    # with drop_incorrectly_named_samples=False, not all Peptide values are filled
    assert "RG7" in df["Peptide"].values


def test_run_all_explicitly_keep_buffers():
    df = test_tidy_data(
        to_glob=_parent_dir+"/test_data/*.csv",
        file_reader_kwargs={},
        drop_incorrectly_named_samples=True,
        drop_buffers=False,
    )

    assert "RG7" in df["Peptide"].values

    assert len(nd._identify_buffer_measurements(df)) > 0

    
def test_nanodrop_data_nonmatching_column_names():
    # bad_input contains a file without the "Sample ID" category
    # all samples from that file will be dropped, but an extra empty column makes it into the output
    file_list = glob.glob(_parent_dir+"/test_data/bad_input/*.tsv")
    with pytest.warns(UserWarning):
        df = nd.tidy_data(file_list,
                                    drop_incorrectly_named_samples=True)
        
    float_cols = [
        "Abs 350",
        "Abs 600",
        "Peptide concentration (uM)",
        "RNA/Peptide Ratio",
    ]
    for col in float_cols:
        assert df[col].dtype == float
        
    for peptide in df["Peptide"].values:
        assert "RG" in peptide