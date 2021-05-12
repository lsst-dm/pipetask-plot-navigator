

import panel
import asyncio
import os

import lsst.daf.butler as dafButler

from RubinTemplate import RubinTemplate
from ButlerSelector import ButlerDatasetSelector
from ButlerWidgets import CollectionSelectWidget, PlotFilterWidget, PlotSelectWidget, VisitWidget

panel.extension()

displayed_visit = 1
plot_pane = panel.GridBox(ncols=1)

butler = dafButler.Butler(config="test_repo/butler.yaml")

butler_selector = ButlerDatasetSelector(butler)
counter_widget = VisitWidget(butler_selector)
plot_collection = CollectionSelectWidget(butler_selector)
plot_filter = PlotFilterWidget(butler_selector)
plot_select = PlotSelectWidget(butler_selector)

def update_image():

    plot_pane.objects = [panel.pane.PNG(butler.datastore.getURI(ref), width=600)
                         for ref in butler_selector.get_selected_plot_datarefs()]
    displayed_visit = counter_widget.value

def poll_next_image():
    if(autoadvance.value == False):
        return

    if(butler_selector.check_if_next_visit_exists()):
        counter_widget.value = str(int(counter_widget.value) + 1)
        update_image()


autoadvance = panel.widgets.Checkbox(name="Auto-advance", value=False)
panel.state.add_periodic_callback(poll_next_image, period=1000, start=True)



update_image()
butler_selector.add_notify_list(update_image)


template = RubinTemplate()

template.sidebar.append(counter_widget)
template.sidebar.append(autoadvance)
template.sidebar.append(plot_collection)
template.sidebar.append(plot_filter)
template.sidebar.append(plot_select)

template.main.append(plot_pane)

template.servable()





