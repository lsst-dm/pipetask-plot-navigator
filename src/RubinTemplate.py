
import pathlib
import panel


class RubinTemplate(panel.template.BootstrapTemplate):


    page_links = {"dashboard_gen3": "Tract-based plots",
                  "visit_dashboard": "Visit-based plots",
                  "single_plot": "Single plot"}

    def __init__(self, **kwargs):
        if("title" not in kwargs):
            kwargs["title"] = "Rubin Plot Navigator"

        if("favicon" not in kwargs):
            kwargs["favicon"] = "/assets/rubin-favicon-transparent-32px.png"

        super().__init__(**kwargs)

        self.header_background = "#1f2121"
        self.header_color = "#058b8c"

        for key, val in self.page_links.items():
            if(panel.state.app_url.lstrip("/") == key):
                self.header.append(panel.pane.HTML(f"<div class=\"header_link header_selected\" href=\"/{key}\">{val}</div>"))
            else:
                self.header.append(panel.pane.HTML(f"<a class=\"header_link\" href=\"/{key}\">{val}</a>"))


        with open("bootstrap_override.css") as f:
            self.config.raw_css.append(f.read())

# The panel template system goes haywire if this doesn't exist.
class RubinDefaultTheme(panel.template.theme.DefaultTheme):

    _template = RubinTemplate

