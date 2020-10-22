import sys

import pandas as pd
import panel as pn

from navigator.config import categories, filters, datastyles
from navigator.gui import get_numbers, get_plots_list
from navigator.parse import get_df

pn.extension()

repo_input = pn.widgets.TextInput(name="Repository", value="")

df = get_df(repo_input.value)

gspec = pn.GridSpec(sizing_mode="stretch_height", max_height=800)

allowed_categories = {"coadd": categories, "visit": categories[:-1]}

filter_select = pn.widgets.Select(name="Filter", options=filters, value=filters[0])
datastyle_select = pn.widgets.RadioButtonGroup(name="Data style", options=datastyles, value=datastyles[0])
category_select = pn.widgets.RadioButtonGroup(name="Category", options=categories)
number_select = pn.widgets.Select(
    name="Tract/Visit number", options=get_numbers(df, filters[0], datastyles[0])
)
compare_toggle = pn.widgets.Toggle(name="Compare?")

debug_text = pn.widgets.StaticText(value="debug")

plot_names = pn.widgets.MultiSelect(
    name="Plots",
    options=get_plots_list(
        df,
        filter_select.value,
        datastyle_select.value,
        number_select.value,
        category_select.value,
        compare_toggle.value,
    ),
)

plots = pn.Column([debug_text])


def update_df(event):
    global df
    df = get_df(repo_input.value)
    update_categories(event)
    update_plot_names(event)

repo_input.param.watch(update_df, "value")


def update_categories(event):
    category_select.options = allowed_categories[datastyle_select.value]
    number_select.options = get_numbers(df, filter_select.value, datastyle_select.value)


datastyle_select.param.watch(update_categories, "value")


def update_plot_names(event):
    debug_text.value = len(df)

    plot_names.options = get_plots_list(
        df,
        filter_select.value,
        datastyle_select.value,
        number_select.value,
        category_select.value,
        compare_toggle.value,
    )


filter_select.param.watch(update_plot_names, "value")
datastyle_select.param.watch(update_plot_names, "value")
category_select.param.watch(update_plot_names, "value")
number_select.param.watch(update_plot_names, "value")
compare_toggle.param.watch(update_plot_names, "value")
repo_input.param.watch(update_plot_names, 'value')


def update_plots(event):
    debug_text.value = event.new
    if isinstance(event.new, list):
        plots.objects = [pn.pane.HTML(f"{v}") for v in event.new]
    else:
        pass
        # plots.objects = [pn.pane.HTML(f"{event.new}: {v}") for v in options.value]


plot_names.param.watch(update_plots, "value")
repo_input.param.watch(update_plots, "value")

gspec[0, 0] = repo_input
gspec[1, 0] = filter_select
gspec[2, 0] = datastyle_select
gspec[3, 0] = category_select
gspec[4, 0] = number_select
gspec[5, 0] = compare_toggle
gspec[6:16, 0] = plot_names
gspec[0, 1] = debug_text
gspec[1:, 1:] = plots

gspec.servable()
