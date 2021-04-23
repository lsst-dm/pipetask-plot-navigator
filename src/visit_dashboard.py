

import panel
import asyncio
import os

import lsst.daf.butler as dafButler

panel.extension()

displayed_visit = 1
counter_widget = panel.widgets.TextInput(name="Latest visit",
                                         value=str(displayed_visit))
plot_pane = panel.GridBox(ncols=1)

butler = dafButler.Butler(config="test_repo/butler.yaml", run="test_run")


def update_image():
    next_visit = "file_{:03d}".format(int(counter_widget.value))
    uri = butler.getURI("visitPlot_demo", visit=int(counter_widget.value),
                     instrument="HSC")
    plot_pane.objects = [panel.pane.PNG(uri, width=600)]
    displayed_visit = counter_widget.value

def poll_next_image():

    next_visit = int(counter_widget.value) + 1
    try:
        if(butler.datasetExists("visitPlot_demo", visit=next_visit,
                                instrument="HSC")):
            counter_widget.value = str(int(counter_widget.value) + 1)
            update_image()
    except LookupError:
        pass


panel.state.add_periodic_callback(poll_next_image, period=1000, start=True)

widget_column = panel.Column(counter_widget, plot_pane)

update_image()
widget_column.servable()






