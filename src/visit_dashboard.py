

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
    try:
        uri = butler.getURI("visitPlot_demo", visit=int(counter_widget.value),
                         instrument="HSC")
    except KeyError:
        return
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

update_image()


bootstrap = panel.template.BootstrapTemplate(title="Rubin Plot Navigator",
                                             favicon="/assets/rubin-favicon-transparent-32px.png")

bootstrap.sidebar.append(counter_widget)
bootstrap.main.append(plot_pane)

with open("bootstrap_override.css") as f:
    bootstrap.config.raw_css.append(f.read())

bootstrap.header_background = "#1f2121"
bootstrap.header_color = "#058b8c"
bootstrap.header.append(panel.pane.HTML("<a class=\"header_link\" href=\"/dashboard_gen3\">Tract-based plots</div>"))
bootstrap.header.append(panel.pane.HTML("<div class=\"header_link header_selected\">Visit-based plots</div>"))


bootstrap.servable()






