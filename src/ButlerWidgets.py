
import panel

class TractListWidget(panel.widgets.MultiSelect):

    def __init__(self, butler_selector, name="Tract", **kwargs):
        super().__init__(name=name, **kwargs)
        self.selector = butler_selector
        self.param.watch(self.tract_updated_event, "value")
        self.selector.add_notify_list(self.selector_updated)

    def tract_updated_event(self, event):
        self.selector.select_tracts(self.value)

    def selector_updated(self):
        self.options = self.selector.get_tract_options()


class CollectionSelectWidget(panel.widgets.AutocompleteInput):

    def __init__(self, butler_selector, name="Collection", **kwargs):
        super().__init__(name=name, **kwargs)
        self.selector = butler_selector
        self.selector_updated()
        self.param.watch(self.collection_updated_event, "value")
        self.selector.add_notify_list(self.selector_updated)

    def collection_updated_event(self, event):
        self.selector.select_collection(self.value)

    def selector_updated(self):
        self.options = self.selector.get_collection_options()
        if(len(self.options) > 0):
            self.value = self.options[0]


class PlotFilterWidget(panel.widgets.TextInput):

    def __init__(self, butler_selector, name="Plot name filter", **kwargs):
        super().__init__(name=name, **kwargs)
        self.selector = butler_selector
        self.param.watch(self.filter_updated_event, "value")

    def filter_updated_event(self, event):
        self.selector.set_plot_filter(self.value)


class PlotSelectWidget(panel.widgets.MultiSelect):

    def __init__(self, butler_selector, name="Plots", **kwargs):
        super().__init__(name=name, **kwargs)
        self.selector = butler_selector
        self.selector_updated()
        self.param.watch(self.plot_name_updated_event, "value")
        self.selector.add_notify_list(self.selector_updated)

    def plot_name_updated_event(self, event):
        self.selector.select_plot_names(self.value)

    def selector_updated(self):
        self.options = self.selector.get_plot_name_options()
