"""Tests wrangling/nanodrop/tidy_data

Contents
--------
test_data/ : sample nanodrop data
test_nanodrop_with_hypothesis : a test using the hypothesis library
test_nanodrop : tests individual functions in nanodrop, excluding tidy_data()
test_tidy_data : tests nandrop.tidy_data(), takes several seconds to complete
"""

from . import test_nanodrop, test_tidy_data, test_nanodrop_with_hypothesis