
import panel

import lsst.daf.butler as dafButler

panel.extension()

plot_pane = panel.GridBox(ncols=1)

dataId_keys = ["tract", "visit"]


def load_image():
    query_params = panel.state.session_args
    # Query parameter values are returned as lists
    collection = query_params.get("collection", [""])[0]
    plot_name = query_params.get("plot_name", [""])[0].decode()

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

bootstrap = panel.template.BootstrapTemplate(title="Rubin Plot Navigator",
                                             favicon="/assets/rubin-favicon-transparent-32px.png")

bootstrap.main.append(error_text)
bootstrap.main.append(plot_pane)

with open("bootstrap_override.css") as f:
    bootstrap.config.raw_css.append(f.read())

bootstrap.header_background = "#1f2121"
bootstrap.header_color = "#058b8c"
bootstrap.header.append(panel.pane.HTML("<a class=\"header_link\" href=\"/dashboard_gen3\">Tract-based plots</div>"))
bootstrap.header.append(panel.pane.HTML("<a class=\"header_link\" href=\"/visit_dashboard\">Visit-based plots</a>"))
bootstrap.header.append(panel.pane.HTML("<div class=\"header_link header_selected\">Single plot</div>"))


bootstrap.servable()

