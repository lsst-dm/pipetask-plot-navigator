"""
Dashboard for pipetask-plot-navigator


"""
import os
import sys
import logging
import time

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
default_collection = os.environ.get("BUTLER_DEFAULT_COLLECTION", None)

try:
    repo_args = pn.state.session_args.get('repo')
    if(repo_args is not None):
        default_repo = repo_args[0].decode()
except Exception as e:
    log.error(e)

log.info("Starting with repo {:s}".format(default_repo))

try:
    coll_args = pn.state.session_args.get('collection')
    if(coll_args is not None):
        default_collection = coll_args[0].decode()
except Exception as e:
    log.error(e)

log.info("Starting with collection {:s}".format(default_collection))

if(len(dafButler.Butler.get_known_repos()) == 0 and repo_config_string is None):
    log.error("No butler repo aliases configured, must set environment variable BUTLER_URI with butler config path.")
    sys.exit(0)


config = None
butler = None
registry = None
plot_types = None
collections = []

plot_paths = {}
plot_datasettypes = {}


pn.extension()

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

known_repos = list(dafButler.Butler.get_known_repos())
known_repos.sort()
repo_select = pn.widgets.Select(name="Repo", options=known_repos)

all_collections = pn.widgets.Checkbox(name="Show all collections")
all_collections.value = False
collection_select = pn.widgets.AutocompleteInput(name="Collection", options=collections)

skymap_select = pn.widgets.Select(name="Skymap")
instrument_select = pn.widgets.Select(name="Instrument")

tract_select = pn.widgets.MultiSelect(name="Tract", options=[], size=8,
        stylesheets=["select.bk-input { background-image: none;}"])
visit_select = pn.widgets.MultiSelect(name="Visit", options=[], size=8,
        stylesheets=["select.bk-input { background-image: none;}"])
plot_filter = pn.widgets.TextInput(name="Plot name filter", value="")
detector_select = pn.widgets.IntInput(
    name="Detector Number", start=0, end=210, step=1, value=0)

plot_select = pn.widgets.MultiSelect(name="Plots", options=[], size=12,
        stylesheets=["select.bk-input { overflow-x: scroll; background-image: none;}"])

debug_text = pn.widgets.StaticText(value="")

width_entry = pn.widgets.IntInput(
    name="Plot width", start=300, end=1200, step=50, value=600
)
ncols_entry = pn.widgets.IntInput(name="n_cols", start=1, end=4, step=1, value=2)
# width_slider = pn.widgets.IntSlider(name='Plot width', start=400, end=1200, step=50, value=600)
# ncols_slider = pn.widgets.IntSlider(name='Number of columns', start=1, end=4, step=1, value=2)

plots = pn.GridBox(["Plots will show up here when selected."], ncols=2)


def find_types(registry, storageClassName="Plot"):
    func_start = time.perf_counter()
    types = []
    for t in registry.queryDatasetTypes():
        try:
            if t.storageClass.name == storageClassName:
                types.append(t)
        except KeyError:
            # If we don't have the code for a given StorageClass in the environment,
            # this test will throw a key error.
            pass

    log.info("find_types duration: {:f}s".format(time.perf_counter() - func_start) )
    return types

def update_butler(event):
    global config
    global butler
    global registry
    global plot_types

    try:
        butler = dafButler.Butler(config=repo_select.value)
        registry = butler.registry

        func_start = time.perf_counter()
        if(all_collections.value):
            collections = list(registry.queryCollections())
            collections.sort()
        else:
            chains = set(butler.registry.queryCollections(collectionTypes={dafButler.CollectionType.CHAINED}))
            # rest = {r for r in butler.registry.queryCollections(collectionTypes={dafButler.CollectionType.RUN, dafButler.CollectionType.TAGGED}) if not any(r.startswith(c) for c in chains)}
            rest = []
            collections = list(chains) + list(rest)
            collections.sort()
        log.info("Finished getting collections {:f}s".format(time.perf_counter() - func_start))

        plot_types = find_types(registry)


        debug_text.value = "Successfully loaded butler."
    except Exception as e:
        debug_text.value = f"Failed to load Butler: {str(e)}"
        log.error(f"Failed to load butler: {str(e)}")
        return

    collection_select.options = collections

    if default_collection is not None and default_collection in collections:
        collection_select.value = default_collection
    else:
        collection_select.value = collections[0]

    skymap_select.options = [x.name for x in registry.queryDimensionRecords("skymap")]
    instrument_select.options = [x.name for x in registry.queryDimensionRecords("instrument")]

if default_repo is not None:
    repo_select.value = default_repo
update_butler(None)



def find_refs(collection, types, required_dimension=None):
    func_start = time.perf_counter()
    if(len(collection) == 0):
        return []
    else:
        collection_summary = registry.getCollectionSummary(collection)
        if required_dimension is not None:
            available_plot_types = [x for x in list(collection_summary.dataset_types) if x.storageClass_name == "Plot" and required_dimension in x.dimensions]
        else:
            available_plot_types = [x for x in list(collection_summary.dataset_types) if x.storageClass_name == "Plot"]

        log.debug("Avaialble plots: {:d}".format(len(available_plot_types)))
        datasets = registry.queryDatasets(available_plot_types, collections=collection, findFirst=True)
        log.info("END find_refs {:f}s".format(time.perf_counter() - func_start))
        return list(datasets)


def update_tract_select(event):
    global registry

    if registry is None or collection_select.value is None:
        return

    refs = find_refs(collection_select.value, [t for t in plot_types if 'tract' in t.dimensions], required_dimension="tract")

    tract_select.options = get_tracts(refs, skymap_select.value)
    tract_select.value = []


def update_visit_select(event):
    global registry

    if registry is None or collection_select.value is None:
        return

    if registry is not None:

        refs = find_refs(collection_select.value, [t for t in plot_types if 'visit' in t.dimensions], required_dimension="visit")

        visit_select.options = get_visits(refs, instrument_select.value)
        visit_select.value = []


def update_url(event):
    prefix = pn.state.location.href.split('?')[0]
    link_text_input.value = f"{prefix:s}?repo={repo_select.value:s}&collection={collection_select.value:s}"


repo_select.param.watch(update_butler, "value")
all_collections.param.watch(update_butler, "value")

collection_select.param.watch(update_tract_select, "value")
skymap_select.param.watch(update_tract_select, "value")

instrument_select.param.watch(update_visit_select, "value")
collection_select.param.watch(update_visit_select, "value")

collection_select.param.watch(update_url, "value")



def update_plot_names(event):
    global plot_paths, plot_datasettypes, plot_select

    plot_names = []
    plot_refs = []

    if visit_tract_tabs.active == 0:
        func_start = time.perf_counter()
        for tract in tract_select.value:
            refs = [
                ref
                for ref in registry.queryDatasets(
                    [t for t in plot_types if 'tract' in t.dimensions],
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
        log.info("END update_plot_names tracts {:f}s".format(time.perf_counter() - func_start))

    elif visit_tract_tabs.active == 1:

        func_start = time.perf_counter()
        for visit in visit_select.value:

            refs = list(
                registry.queryDatasets(
                    [t for t in plot_types if 'visit' in t.dimensions],
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
        log.info("END update_plot_names visits {:f}s".format(time.perf_counter() - func_start))

    elif visit_tract_tabs.active == 2:
        # Detector
        func_start = time.perf_counter()
        refs = list(
            registry.queryDatasets(
                [t for t in plot_types if 'detector' in t.dimensions and 'visit' not in t.dimensions and 'tract' not in t.dimensions],
                collections=collection_select.value,
                findFirst=True,
                dataId={"instrument": instrument_select.value, "detector": detector_select.value},
            )
        )

        if len(plot_filter.value) > 0:
            refs = filter(
                lambda ref: re.search(plot_filter.value, ref.datasetType.name), refs
            )

        names = [
            (f"{p.datasetType.name}", p.datasetType.name) for p in refs
        ]

        plot_refs.extend(refs)
        plot_names.extend(names)
        log.info("END update_plot_names detector {:f}s".format(time.perf_counter() - func_start))

    elif visit_tract_tabs.active == 3:

        # Instrument/Global plots
        # If we had collections with plots from multiple instruments we would
        # need to have a selector for that, but in practice that very uncommon.
        func_start = time.perf_counter()

        inst_ds_types = [t for t in plot_types if 'detector' not in t.dimensions and 'visit' not in t.dimensions and 'tract' not in t.dimensions]
        refs = list(
            registry.queryDatasets(
                inst_ds_types,
                collections=collection_select.value,
                findFirst=True
            )
        )

        if len(plot_filter.value) > 0:
            refs = filter(
                lambda ref: re.search(plot_filter.value, ref.datasetType.name), refs
            )

        names = [
            (f"{p.datasetType.name}", p.datasetType.name) for p in refs
        ]

        plot_refs.extend(refs)
        plot_names.extend(names)
        log.info("END update_plot_names instrument {:f}s".format(time.perf_counter() - func_start))

    plot_paths = {
        name[0]: butler.getURI(ref)
        for name, ref in zip(plot_names, plot_refs)
    }

    plot_datasettypes = {name[0]: name[1] for name in plot_names}

    plot_names.sort()
    plot_select.options = list(plot_paths.keys())


collection_select.param.watch(update_plot_names, "value")
plot_filter.param.watch(update_plot_names, "value")
tract_select.param.watch(update_plot_names, "value")
visit_select.param.watch(update_plot_names, "value")
detector_select.param.watch(update_plot_names, "value")
instrument_select.param.watch(update_plot_names, "value")


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
show_link_button = pn.widgets.Toggle(name="Show Link")
link_text_input = pn.widgets.TextInput(disabled=True, value="URL", visible=False)
update_url(None)


def refresh(event):

    if visit_tract_tabs.active == 0:
        update_tract_select(event)
    else:
        update_visit_select(event)

    update_plot_names(event)

    plots.objects = [get_png(name) for name in plot_select.value]


refresh_button.on_click(refresh)

def update_link_visibility(event):
    link_text_input.visible = show_link_button.value

show_link_button.param.watch(update_link_visibility, "value")



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
    ("Tract", pn.Column(skymap_select, tract_select, next_prev_tract_row)),
    ("Visit", pn.Column(instrument_select, visit_select, next_prev_visit_row)),
    ("Detector", pn.Column(instrument_select, detector_select)),
    ("Global", pn.Column()),
)
visit_tract_tabs.dynamic = True
visit_tract_tabs.param.watch(update_plot_names, "active")

bootstrap.sidebar.append(repo_select)
bootstrap.sidebar.append(collection_select)
bootstrap.sidebar.append(all_collections)

refresh_row = pn.Row(refresh_button, show_link_button)
bootstrap.sidebar.append(refresh_row)

bootstrap.sidebar.append(link_text_input)
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
