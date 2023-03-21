"""
Dashboard for pipetask-plot-navigator


"""
import os
import sys
import logging

# Configure logging
log = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s [%(name)-12s] %(levelname)-8s %(message)s")
handler.setFormatter(formatter)
log.addHandler(handler)
try:
    log.setLevel(os.environ["LOG_LEVEL"].upper())
except:
    log.setLevel("DEBUG")

from pathlib import Path
import re
import panel as pn
from IPython.display import Image

import lsst.daf.butler as dafButler

repo_config_string = os.environ.get("BUTLER_URI", None)
default_repo = os.environ.get("BUTLER_DEFAULT_REPO", None)

if(len(dafButler.Butler.get_known_repos()) == 0 and repo_config_string is None):
    print("No butler repo aliases configured, must set environment variable BUTLER_URI with butler config path.")
    sys.exit(0)


config = None
butler = None
registry = None
collections = []

plot_paths = {}
plot_datasettypes = {}


pn.extension()


def initialize():
    global config, butler, registry, collections

    global plot_paths

    config = None
    butler = None
    registry = None
    collections = []

    plot_paths = {}


def get_tracts(refs, skymap):
    tracts = list(
        set(
            r.dataId["tract"]
            for r in refs
            if ("tract" in r.dataId) & (r.dataId.get("skymap", "") == skymap)
        )
    )
    tracts.sort()
    return tracts


def get_visits(refs, instrument):
    visits = list(
        set(
            r.dataId["visit"]
            for r in refs
            if (("visit" in r.dataId) & (r.dataId.get("instrument", "") == instrument))
        )
    )
    visits.sort()
    return visits

repo_select = pn.widgets.Select(name="Repo", options=list(dafButler.Butler.get_known_repos()))

collection_select = pn.widgets.AutocompleteInput(name="Collection", options=collections)

skymap_select = pn.widgets.Select(name="Skymap", options=["hsc_rings_v1", "DC2"])
instrument_select = pn.widgets.Select(
    name="Instrument", options=["HSC", "LATISS", "LSSTCam-imSim"]
)
tract_select = pn.widgets.MultiSelect(name="Tract", options=[], size=8)
visit_select = pn.widgets.MultiSelect(name="Visit", options=[], size=8)
plot_filter = pn.widgets.TextInput(name="Plot name filter", value="")

plot_select = pn.widgets.MultiSelect(name="Plots", options=[], size=12)

debug_text = pn.widgets.StaticText(value="")

width_entry = pn.widgets.IntInput(
    name="Plot width", start=300, end=1200, step=50, value=600
)
ncols_entry = pn.widgets.IntInput(name="n_cols", start=1, end=4, step=1, value=2)
# width_slider = pn.widgets.IntSlider(name='Plot width', start=400, end=1200, step=50, value=600)
# ncols_slider = pn.widgets.IntSlider(name='Number of columns', start=1, end=4, step=1, value=2)

plots = pn.GridBox(["Plots will show up here when selected."], ncols=2)


def update_butler(event):
    global config
    global butler
    global registry

    try:
        butler = dafButler.Butler(config=repo_select.value)
        registry = butler.registry
        collections = list(registry.queryCollections())
        collection_select.options = collections
        collection_select.value = collections[0]

        debug_text.value = "Successfully loaded butler."
    except Exception as e:
        debug_text.value = f"Failed to load Butler: {str(e)}"
        log.error(f"{str(e)}")

if default_repo is not None:
    repo_select.value = default_repo
update_butler(None)


def find_types(registry, storageClassName="Plot"):
    types = []
    for t in registry.queryDatasetTypes():
        try:
            if t.storageClass.name == storageClassName:
                types.append(t)
        except KeyError:
            # If we don't have the code for a given StorageClass in the environment,
            # this test will throw a key error.
            pass

    return types


def find_refs(collection, types):
    return list(registry.queryDatasets(types, collections=collection, findFirst=True))


def update_tract_select(event):
    global registry

    types = find_types(registry)
    if registry is not None:
        refs = find_refs(collection_select.value, types)

        tract_select.options = get_tracts(refs, skymap_select.value)
        tract_select.value = []


def update_visit_select(event):
    global registry

    types = find_types(registry)
    if registry is not None:

        refs = find_refs(collection_select.value, types)

        visit_select.options = get_visits(refs, instrument_select.value)
        visit_select.value = []


repo_select.param.watch(update_butler, "value")

collection_select.param.watch(update_tract_select, "value")
skymap_select.param.watch(update_tract_select, "value")

instrument_select.param.watch(update_visit_select, "value")
collection_select.param.watch(update_visit_select, "value")


def update_plot_names(event):
    global plot_paths, plot_datasettypes

    plot_names = []
    plot_refs = []
    types = find_types(registry)

    if visit_tract_tabs.active == 0:
        for tract in tract_select.value:
            refs = [
                ref
                for ref in registry.queryDatasets(
                    types,
                    collections=collection_select.value,
                    findFirst=True,
                    dataId={"skymap": skymap_select.value, "tract": tract},
                )
                if re.search(plot_filter.value, ref.datasetType.name)
            ]
            refs.sort(key=lambda x: x.datasetType.name)
            names = [
                (f"{p.datasetType.name} ({tract})", p.datasetType.name) for p in refs
            ]

            plot_refs.extend(refs)
            plot_names.extend(names)
    else:
        for visit in visit_select.value:

            refs = list(
                registry.queryDatasets(
                    types,
                    collections=collection_select.value,
                    findFirst=True,
                    dataId={"instrument": instrument_select.value, "visit": visit},
                )
            )

            if len(plot_filter.value) > 0:
                refs = filter(
                    lambda ref: re.search(plot_filter.value, ref.datasetType.name), refs
                )

            names = [
                (f"{p.datasetType.name} ({visit})", p.datasetType.name) for p in refs
            ]

            plot_refs.extend(refs)
            plot_names.extend(names)

    plot_paths = {
        name[0]: butler.getURI(ref, collections=collection_select.value)
        for name, ref in zip(plot_names, plot_refs)
    }

    plot_datasettypes = {name[0]: name[1] for name in plot_names}

    plot_names.sort()
    plot_select.options = list(plot_paths.keys())


collection_select.param.watch(update_plot_names, "value")
plot_filter.param.watch(update_plot_names, "value")
tract_select.param.watch(update_plot_names, "value")
visit_select.param.watch(update_plot_names, "value")


def get_png(name):
    return pn.pane.PNG(Image(data=plot_paths[name].read()), width=width_entry.value)


def update_plots(event):
    plots.objects = [get_png(name) for name in event.new]


plot_select.param.watch(update_plots, "value")


def update_plot_layout(event):

    for plot in plots:
        plot.width = width_entry.value

    plots.ncols = ncols_entry.value


width_entry.param.watch(update_plot_layout, "value")
ncols_entry.param.watch(update_plot_layout, "value")

refresh_button = pn.widgets.Button(name="Reload", button_type="default")


def refresh(event):

    if visit_tract_tabs.active == 0:
        update_tract_select(event)
    else:
        update_visit_select(event)

    update_plot_names(event)

    plots.objects = [get_png(name) for name in plot_select.value]


refresh_button.on_click(refresh)


bootstrap = pn.template.BootstrapTemplate(
    title="Rubin Plot Navigator", favicon="assets/rubin-favicon-transparent-32px.png"
)


# Multiple collections are temporarily disabled.
#
# repo_collection_tabs = pn.Tabs(('Collection 1', pn.Column(collection_select)),
#                                ('Collection 2', pn.Column(collection2_select)))


def next_visit(event):
    selected_plot_datasets = set(plot_datasettypes[x] for x in plot_select.value)
    increment_visit(increment=1)
    plot_select.value = [
        plot_name
        for plot_name in plot_select.options
        if plot_name.split(" ")[0] in selected_plot_datasets
    ]


def prev_visit(event):
    selected_plot_datasets = set(plot_datasettypes[x] for x in plot_select.value)
    increment_visit(increment=-1)
    plot_select.value = [
        plot_name
        for plot_name in plot_select.options
        if plot_name.split(" ")[0] in selected_plot_datasets
    ]


def increment_visit(increment=1):
    if len(visit_select.value) == 0:
        return

    # If there are multiple selections, take the last one
    selected_visit = visit_select.value[-1]

    selected_visit_index = visit_select.options.index(selected_visit)
    if (selected_visit_index > 0) and (
        selected_visit_index < (len(visit_select.options) + 1)
    ):
        visit_select.value = [visit_select.options[selected_visit_index + increment]]


def next_tract(event):
    selected_plot_datasets = set(plot_datasettypes[x] for x in plot_select.value)
    increment_tract(increment=1)
    plot_select.value = [
        plot_name
        for plot_name in plot_select.options
        if plot_name.split(" ")[0] in selected_plot_datasets
    ]


def prev_tract(event):
    selected_plot_datasets = set(plot_datasettypes[x] for x in plot_select.value)
    increment_tract(increment=-1)
    plot_select.value = [
        plot_name
        for plot_name in plot_select.options
        if plot_name.split(" ")[0] in selected_plot_datasets
    ]


def increment_tract(increment=1):
    if len(tract_select.value) == 0:
        return

    # If there are multiple selections, take the last one
    selected_tract = tract_select.value[-1]

    selected_tract_index = tract_select.options.index(selected_tract)
    if (selected_tract_index > 0) and (
        selected_tract_index < (len(tract_select.options) + 1)
    ):
        tract_select.value = [tract_select.options[selected_tract_index + increment]]


next_visit_button = pn.widgets.Button(name="Next Visit", width=80)
prev_visit_button = pn.widgets.Button(name="Prev Visit", width=80)
next_prev_visit_row = pn.Row(prev_visit_button, next_visit_button)
next_visit_button.on_click(next_visit)
prev_visit_button.on_click(prev_visit)

next_tract_button = pn.widgets.Button(name="Next Tract", width=80)
prev_tract_button = pn.widgets.Button(name="Prev Tract", width=80)
next_prev_tract_row = pn.Row(prev_tract_button, next_tract_button)
next_tract_button.on_click(next_tract)
prev_tract_button.on_click(prev_tract)

visit_tract_tabs = pn.Tabs(
    ("Tracts", pn.Column(skymap_select, tract_select, next_prev_tract_row)),
    ("Visits", pn.Column(instrument_select, visit_select, next_prev_visit_row)),
)
visit_tract_tabs.param.watch(update_plot_names, "active")

bootstrap.sidebar.append(repo_select)
bootstrap.sidebar.append(collection_select)
bootstrap.sidebar.append(refresh_button)
bootstrap.sidebar.append(visit_tract_tabs)
bootstrap.sidebar.append(plot_filter)
bootstrap.sidebar.append(plot_select)

bootstrap.sidebar.append(width_entry)
bootstrap.sidebar.append(ncols_entry)

bootstrap.main.append(debug_text)

# Multiple collections are temporarily disabled.
#
# bootstrap.main.append(pn.Tabs(('collection 1', plots), ('collection 2', plots2)))
bootstrap.main.append(plots)


with open("bootstrap_override.css") as f:
    bootstrap.config.raw_css.append(f.read())

bootstrap.header_background = "#1f2121"
bootstrap.header_color = "#058b8c"


bootstrap.servable()
