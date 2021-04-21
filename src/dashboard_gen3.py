"""
Dashboard for pipetask-plot-navigator


"""
import os
import logging

from ButlerWidgets import TractListWidget, CollectionSelectWidget, PlotFilterWidget, PlotSelectWidget
from ButlerSelector import ButlerDatasetSelector

# Configure logging
log = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s [%(name)-12s] %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
log.addHandler(handler)
try:
    log.setLevel(os.environ['LOG_LEVEL'].upper())
except:
    log.setLevel('DEBUG')

from pathlib import Path
import re
import panel as pn

import lsst.daf.butler as dafButler

butler_selector = ButlerDatasetSelector(None)
config = None
butler = None
registry = None
collections = []

config2 = None
butler2 = None
registry2 = None
collections2 = []

pattern = re.compile(".*Plot.*")
plot_paths = {}
plot_paths2 = {}


pn.extension()

def initialize():
    global config, butler, registry, collections
    global config2, butler2, registry2, collections2

    global plot_paths, plot_paths2
    
    config = None
    butler = None
    registry = None
    collections = []
    
    config2 = None
    butler2 = None
    registry2 = None
    collections2 = []
    
    plot_paths = {}
    plot_paths2 = {}
    
def get_tracts(refs):
    tracts = list(set(r.dataId["tract"] for r in refs))
    tracts.sort()
    return tracts


root_entry = pn.widgets.TextInput(name="Repo root directory", value="/project/hsc/gen3repo")
repo_select = pn.widgets.Select(
    name="Repository",
    options=[p for p in Path(root_entry.value).glob("*") if p.joinpath("butler.yaml").exists()],
    value=None,
)
collection_select = CollectionSelectWidget(butler_selector)
repo2_select = pn.widgets.Select(
    name="Repository 2",
    options=['None'] + [p for p in Path(root_entry.value).glob("*") if p.joinpath("butler.yaml").exists()],
    value=None,
)
collection2_select = pn.widgets.AutocompleteInput(name="Collection 2", options=collections2)

tract_select = TractListWidget(butler_selector)
plot_filter = PlotFilterWidget(butler_selector)
plot_select = PlotSelectWidget(butler_selector)

debug_text = pn.widgets.StaticText(value=f"config = {config}")

width_entry = pn.widgets.IntInput(name="Plot width", start=300, end=1200, step=50, value=600)
ncols_entry = pn.widgets.IntInput(name="n_cols", start=1, end=4, step=1, value=2)
# width_slider = pn.widgets.IntSlider(name='Plot width', start=400, end=1200, step=50, value=600)
# ncols_slider = pn.widgets.IntSlider(name='Number of columns', start=1, end=4, step=1, value=2)

plots = pn.GridBox(["Plots will show up here when selected."], ncols=2)
plots2 = pn.GridBox([], ncols=2)

def update_repo_root(event):
    try:
        log.debug(f'Files in root directory: {[p for p in Path(root_entry.value).glob("*")]}')
        repo_options = []
        for p in Path(root_entry.value).glob("*"):
            try:
                if p.joinpath("butler.yaml").exists():
                    repo_options.append(p)
            except Exception as e:
                pass
        repo_select.options = repo_options
        log.debug(f'repo_select.options: {repo_select.options}')
        update_butler(None)
    except Exception as e:
        log.error(f'{str(e)}')
    
root_entry.param.watch(update_repo_root, 'value')

def update_butler(event):
    global config
    global butler
    global registry
    global butler_selector

    try:
        log.debug(f'Repo root directory: {root_entry.value}')
        log.debug(f'Selected repo: {repo_select.value}')
        config = repo_select.value.joinpath("butler.yaml")
        log.debug(f'Butler config: {config}')
        butler = dafButler.Butler(config=str(config))
        butler_selector.set_butler(butler)
        #registry = butler.registry
        #collections = list(registry.queryCollections())
        #collection_select.options = collections
        #collection_select.value = collections[0]

        debug_text.value = f"Successfully loaded butler from {config}."
    except Exception as e:
        debug_text.value = f"Failed to load Butler: {str(e)}"
        log.error(f'{str(e)}')

update_butler(None)

repo_select.param.watch(update_butler, "value")


def update_butler2(event):
    global config2
    global butler2
    global registry2

    try:
        if repo2_select.value == 'None':
            config2 = None
            butler2 = None
            registry2 = None
            collection2_select.options = []
            
            debug_text.value = f"butler2 set to None."
        else:            
            config2 = repo2_select.value.joinpath("butler.yaml")
            butler2 = dafButler.Butler(config=str(config2))
            registry2 = butler2.registry
            collections2 = list(registry2.queryCollections())
            collection2_select.options = collections2
            collection2_select.value = collections2[0]

            debug_text.value = f"Successfully loaded butler2 from {config}."
    except:
        debug_text.value = f"Failed to load butler2 from {config}"
#         collection2_select.value = ""
        raise

# root_entry.param.watch(update_butler2, "value")
# repo2_select.param.watch(update_butler2, "value")


#def update_tract_select(event):
#    global registry
#    
#    if registry is not None:
#        try:
#            refs = list(registry.queryDatasets(pattern, collections=collection_select.value, findFirst=True))
#            if registry2 is not None:
#                refs2 = list(registry2.queryDatasets(pattern, collections=collection2_select.value, findFirst=True))
#            else:
#                refs2 = refs
#
#            tract_select.options = list(set(get_tracts(refs)).intersection(set(get_tracts(refs2))))
#            tract_select.value = []
#        except:
#            debug_text.value += f'; {event.new}'
#             raise
        
#collection_select.param.watch(update_tract_select, "value")
#collection2_select.param.watch(update_tract_select, "value")

def update_plot_names(event):
    global plot_paths, plot_paths2

    plot_names = []
    plot_names2 = []
    plot_refs = []
    plot_refs2 = []
    for tract in tract_select.value:
        refs = [
            ref
            for ref in registry.queryDatasets(
                pattern,
                collections=collection_select.value,
                findFirst=True,
                dataId={"skymap": "hsc_rings_v1", "tract": tract},
            )
            if re.search(plot_filter.value, ref.datasetType.name)
        ]
        names = [f"{p.datasetType.name} ({tract})" for p in refs]

        if registry2 is not None:
            refs2 = [
                ref
                for ref in registry2.queryDatasets(
                    pattern,
                    collections=collection2_select.value,
                    findFirst=True,
                    dataId={"skymap": "hsc_rings_v1", "tract": tract},
                )
                if re.search(plot_filter.value, ref.datasetType.name)
            ]
            names2 = [f"{p.datasetType.name} ({tract})" for p in refs2]
        else:
            refs2 = refs
            names2 = names
        
        plot_refs.extend(refs)
        plot_refs2.extend(refs2)
        plot_names.extend(names)
        plot_names2.extend(names2)

    plot_paths = {
        name: butler.getURI(ref, collections=collection_select.value).path
        for name, ref in zip(plot_names, plot_refs)
    }
    
    if registry2 is not None:
        plot_paths2 = {
            name: butler2.getURI(ref, collections=collection2_select.value).path
            for name, ref in zip(plot_names2, plot_refs2)
        }

#     debug_text.value = str(plot_names) + '\n' + str(plot_names2)

    plot_names = list(set(plot_names).intersection(plot_names2))
    plot_names.sort()
    plot_select.options = plot_names
        
# collection_select.param.watch(update_plot_names, "value")
# repo2_select.param.watch(update_plot_names, 'value')
# collection2_select.param.watch(update_plot_names, "value")
# plot_filter.param.watch(update_plot_names, "value")
# tract_select.param.watch(update_plot_names, "value")


def get_png(name):
    return pn.pane.PNG(plot_paths[name], width=width_entry.value)

def get_png2(name):
    return pn.pane.PNG(plot_paths2[name], width=width_entry.value)

def update_plots():
    if(len(butler_selector.get_selected_plot_datarefs()) > 0):

        plots.objects = [pn.pane.PNG(butler.datastore.getURI(ref), width=width_entry.value)
            for ref in butler_selector.get_selected_plot_datarefs()]
#     debug_text.value = [plot_paths[name] for name in event.new]    
#    plots.objects = [get_png(name) for name in event.new]
#    if registry2 is not None:
#        plots2.objects = [get_png2(name) for name in event.new]
            
# plot_select.param.watch(update_plots, "value")
butler_selector.add_notify_list(update_plots)

def update_plot_layout(event):
    
#     debug_text.value = str(f'new number is {event.new}')        
    for plot in plots:
        plot.width = width_entry.value
    for plot in plots2:
        plot.width = width_entry.value
    
    plots.ncols = ncols_entry.value
    plots2.ncols = ncols_entry.value    
        
width_entry.param.watch(update_plot_layout, "value")
ncols_entry.param.watch(update_plot_layout, "value")

refresh_button = pn.widgets.Button(name='Reload', button_type='default')

def refresh(event):
    butler_selector.notify_listeners()
    #update_butler(event)
    #update_tract_select(event)
    #update_plot_names(event)
    #plots.objects = [get_png(name) for name in plot_select.value]
    #if registry2 is not None:
    #    plots2.objects = [get_png2(name) for name in plot_select.value]
        
refresh_button.on_click(refresh)


bootstrap = pn.template.BootstrapTemplate(title="Rubin Plot Navigator",
                                             favicon="/assets/rubin-favicon-transparent-32px.png")

repo_collection_tabs = pn.Tabs(('Collection 1', pn.Column(repo_select, collection_select)),
                               ('Collection 2', pn.Column(repo2_select, collection2_select)))


bootstrap.sidebar.append(root_entry)
bootstrap.sidebar.append(repo_collection_tabs)
bootstrap.sidebar.append(refresh_button)
bootstrap.sidebar.append(tract_select)
bootstrap.sidebar.append(plot_filter)
bootstrap.sidebar.append(plot_select)

bootstrap.sidebar.append(width_entry)
bootstrap.sidebar.append(ncols_entry)

bootstrap.main.append(debug_text)
bootstrap.main.append(pn.Tabs(('collection 1', plots), ('collection 2', plots2)))


with open("bootstrap_override.css") as f:
    bootstrap.config.raw_css.append(f.read())

bootstrap.header_background = "#1f2121"
bootstrap.header_color = "#058b8c"
bootstrap.header.append(pn.pane.HTML("<div class=\"header_link header_selected\" >Tract-based plots</div>"))
bootstrap.header.append(pn.pane.HTML("<a class=\"header_link\" href=\"/visit_dashboard\">Visit-based plots</a>"))


bootstrap.servable()


