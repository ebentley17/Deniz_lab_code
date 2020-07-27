"""Scatter function written by Justin Bois, as found in his 
2019 Programming for Biological Sciences Bootcamp.

Modified by Emily Bentley to satisfy deprecation warnings.
2020-06-14: modified to address error when cat=None
2020-06-14: modified to address mutable default argument issue

Original code at: http://justinbois.github.io/bootcamp/2019/lessons/l25_exercise_3.html
"""

import pandas as pd

import bokeh.io
import bokeh.plotting


scatter_palette = [
    "#4e79a7",
    "#f28e2b",
    "#e15759",
    "#76b7b2",
    "#59a14f",
    "#edc948",
    "#ff9da7",
    "#b07aa1",
    "#9c755f",
    "#bab0ac",
]


def scatter(
    data=None,
    cat=None,
    x=None,
    y=None,
    p=None,
    palette=None,
    show_legend=True,
    click_policy="hide",
    marker_kwargs=None,
    **kwargs,
):
    """
    Parameters
    ----------
    data : Pandas DataFrame
        DataFrame containing tidy data for plotting.
    cat : hashable
        Name of column to use as categorical variable.
    x : hashable
        Name of column to use as x-axis.
    y : hashable
        Name of column to use as y-axis.
    p : bokeh.plotting.Figure instance, or None (default)
        If None, create a new figure. Otherwise, populate the existing
        figure `p`.
    palette : list of strings of hex colors, or single hex string
        If a list, color palette to use. If a single string representing
        a hex color, all glyphs are colored with that color. Default is
        the default color cycle employed by Vega-Lite.
    show_legend : bool, default False
        If True, show legend.
    tooltips : list of 2-tuples
        Specification for tooltips as per Bokeh specifications. For
        example, if we want `col1` and `col2` tooltips, we can use
        `tooltips=[('label 1': '@col1'), ('label 2': '@col2')]`. Ignored
        if `formal` is True.
    show_legend : bool, default False
        If True, show a legend.
    click_policy : str, default "hide"
        How to display points when their legend entry is clicked.
    marker_kwargs : dict
        kwargs to be passed to `p.circle()` when making the scatter plot.
    kwargs
        Any kwargs to be passed to `bokeh.plotting.figure()` when making 
        the plot.

    Returns
    -------
    output : bokeh.plotting.Figure instance
        Plot populated with jitter plot or box plot.
    """
    # Automatically name the axes
    if "x_axis_label" not in kwargs:
        kwargs["x_axis_label"] = x
    if "y_axis_label" not in kwargs:
        kwargs["y_axis_label"] = y

    # Instantiate figure
    if p is None:
        p = bokeh.plotting.figure(**kwargs)
    
    if palette is None:
        palette = scatter_palette
    
    if marker_kwargs is None:
        marker_kwargs = {}

    if cat is None:
        p.circle(source=data, x=x, y=y, color=scatter_palette[0], **marker_kwargs)
    
    # Build plot (not using color factors) to enable click policies
    else:
        for i, (name, g) in enumerate(data.groupby(cat, sort=False)):
            marker_kwargs["color"] = palette[i % len(palette)]
            marker_kwargs["legend_label"] = str(name)
            p.circle(source=g, x=x, y=y, **marker_kwargs)
    
        if show_legend:
            p.legend.click_policy = click_policy
        else:
            p.legend.visible = False

    return p