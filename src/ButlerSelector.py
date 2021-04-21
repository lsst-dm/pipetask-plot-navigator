
import re

class ButlerDatasetSelector:

    def __init__(self, butler):
        self.butler = butler
        self.notify_list = []
        self.selected_collection = ""
        self.selected_tracts = ""
        self.plot_filter = ""
        self.selected_plot_names = []

    def add_notify_list(self, func):
        self.notify_list.append(func)

    def notify_listeners(self):
        for notify_func in self.notify_list:
            notify_func()

    def set_butler(self, butler):
        self.butler = butler
        self.notify_listeners()

    def get_collection_options(self):
        if(self.butler is None):
            return []
        collections = list(self.butler.registry.queryCollections())
        return collections

    def select_collection(self, collection):
        self.selected_collection = collection
        self.notify_listeners()

    def get_selected_collection(self):
        return self.selected_collection

    def get_tract_options(self):
        if(self.butler is None):
            return []

        pattern = re.compile(".*Plot.*")
        registry = self.butler.registry
        refs = list(registry.queryDatasets(pattern,
                                           collections=self.get_selected_collection(),
                                           findFirst=True))
        tracts = list(set(r.dataId["tract"] for r in refs))
        return tracts

    def select_tracts(self, tracts):
        self.selected_tracts = tracts
        self.notify_listeners()

    def get_selected_tracts(self):
        return self.selected_tracts

    def set_plot_filter(self, filter_string):
        self.plot_filter = filter_string

    def get_plot_name_options(self):
        plot_options = {}
        pattern = re.compile(".*Plot.*")

        for tract in self.get_selected_tracts():
            query = self.butler.registry.queryDatasets(
                pattern,
                collections=self.get_selected_collection(),
                findFirst=True,
                dataId={"skymap": "hsc_rings_v1", "tract": tract})
            for ref in query:
                if not re.search(self.plot_filter, ref.datasetType.name):
                    continue

                display_string = f"{ref.datasetType.name} ({tract})"
                plot_options[display_string] = ref

        return plot_options

    def select_plot_names(self, plot_names):
        self.selected_plot_names = plot_names
        self.notify_listeners()

    def get_selected_plot_names(self):
        return self.selected_plot_names

    def get_selected_plot_datarefs(self):
        return self.selected_plot_names


