import pandas as pd
import panel as pn

from .config import filters, datastyles, categories, plot_data_path


def get_numbers(df, filt, datastyle):
    if df is None:
        return []

    numbers = list(df.query(f'filt == "{filt}" and datastyle == "{datastyle}"').number.unique())
    numbers.sort()
    return numbers


def get_plots_list(df, filt, datastyle, number, category, compare=False, full_name=False):
    """Returns list of plot names given a datastyle, number, and category, and whether compare
    """
    if df is None:
        return []

    q = f'filt == "{filt}" and datastyle == "{datastyle}" and number == {number} and category == "{category}" and compare == {compare}'
    
    if full_name:
        plots = list(df.query(q).basename)
    else:
        plots = list(df.query(q).content)
    plots.sort()
    return plots
