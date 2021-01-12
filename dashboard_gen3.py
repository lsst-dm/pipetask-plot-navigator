from pathlib import Path
import re
import panel as pn

pn.extension()

import lsst.daf.butler as dafButler

default_repo = Path("/project/hsc/gen3repo/rc2w42_ssw46")

config = default_repo.joinpath("butler.yaml")
butler = dafButler.Butler(config=str(config))
registry = butler.registry
collections = list(registry.queryCollections())

pattern = re.compile(".*Plot.*")
plot_paths = {}

pn.extension()


def get_tracts(refs):
    tracts = list(set(r.dataId["tract"] for r in refs))
    tracts.sort()
    return tracts


root_entry = pn.widgets.TextInput(name="Repo root", value="/project/hsc/gen3repo")
repo_select = pn.widgets.Select(
    name="Repository",
    options=[p for p in Path(root_entry.value).glob("*") if p.joinpath("butler.yaml").exists()],
    value=default_repo,
)
collection_select = pn.widgets.AutocompleteInput(name="Collection", options=collections)
tract_select = pn.widgets.MultiSelect(name="Tract", options=[])
plot_filter = pn.widgets.TextInput(name="Plot name filter", value="")

plot_select = pn.widgets.MultiSelect(name="Plots", options=[],)

debug_text = pn.widgets.StaticText(value=f"config = {config}")


plots = pn.GridBox(["placeholder"], ncols=2)


def update_butler(event):
    global config
    global butler
    global registry

    try:
        config = repo_select.value.joinpath("butler.yaml")
        butler = dafButler.Butler(config=str(config))
        registry = butler.registry
        collections = list(registry.queryCollections())
        collection_select.value = ""

        debug_text.value = f"successfully loaded butler from {config}"
    except:
        debug_text.value = f"Failed to load Butler from {config}"
        collection_select.value = ""


root_entry.param.watch(update_butler, "value")
repo_select.param.watch(update_butler, "value")


def update_tract_select(event):
    refs = list(registry.queryDatasets(pattern, collections=collection_select.value, findFirst=True))
    tract_select.options = get_tracts(refs)
    tract_select.value = []


collection_select.param.watch(update_tract_select, "value")


def update_plot_names(event):
    global plot_paths

    plot_names = []
    plot_refs = []
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

        plot_refs.extend(refs)
        plot_names.extend(names)

    plot_paths = {
        name: butler.getURI(ref, collections=collection_select.value).path
        for name, ref in zip(plot_names, plot_refs)
    }

    plot_names.sort()
    plot_select.options = plot_names


collection_select.param.watch(update_plot_names, "value")
plot_filter.param.watch(update_plot_names, "value")
tract_select.param.watch(update_plot_names, "value")


def get_png(name):
    return pn.pane.PNG(plot_paths[name], width=600)


def update_plots(event):
    #     debug_text.value = [plot_paths[name] for name in event.new]
    plots.objects = [get_png(name) for name in event.new]


plot_select.param.watch(update_plots, "value")

gspec = pn.GridSpec(sizing_mode="stretch_height", max_height=800)

gspec[0, 0] = root_entry
gspec[1, 0] = repo_select
gspec[2, 0] = collection_select
gspec[3, 0] = tract_select
gspec[4, 0] = plot_filter
gspec[5:10, 0] = plot_select
# gspec[0, 1] = debug_text
gspec[1:, 1] = plots

gspec.servable()
