
import panel

import lsst.daf.butler as dafButler
from RubinTemplate import RubinTemplate

panel.extension()

plot_pane = panel.GridBox(ncols=1)

dataId_keys = ["tract", "visit"]


def load_image():
    query_params = panel.state.session_args
    # Query parameter values are returned as lists
    collection = query_params.get("collection", [""])[0]
    plot_name = query_params.get("plot_name", [b""])[0].decode()

    dataId = {"instrument": "HSC"}
    for key in dataId_keys:
        if(key in query_params):
            dataId[key] = int(query_params[key][0])

    butler = dafButler.Butler(config="test_repo/butler.yaml", run="test_run")

    try:
        uri = butler.getURI(plot_name, dataId)
    except (KeyError, LookupError) as e:
        error_text.value = str(e)
        return

    plot_pane.objects = [panel.pane.PNG(uri, width=600)]


error_text = panel.widgets.StaticText(value="", style={"color": "red"}, width=400)
load_image()

template = RubinTemplate()

template.main.append(error_text)
template.main.append(plot_pane)


template.servable()

