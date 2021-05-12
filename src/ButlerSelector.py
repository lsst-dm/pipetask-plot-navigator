
import re
import fnmatch
import lsst.daf.butler as dafButler

class ButlerDatasetSelector:

    def __init__(self, butler):
        self.butler = butler
        self.notify_list = []
        self.visit = 0
        self.selected_collection = ""
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

    def set_visit(self, visit):
        self.visit = visit
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

    def set_plot_filter(self, filter_string):
        self.plot_filter = filter_string

    def get_plot_name_options(self):
        plot_options = {}
        pattern = re.compile(".*Plot.*")

        if(len(self.get_selected_collection()) == 0):
            return []

        query = self.butler.registry.queryDatasets(
            pattern,
            collections=self.get_selected_collection(),
            findFirst=True,
            dataId={"skymap": "hsc_rings_v1"})
        for ref in query:
            if not re.search(self.plot_filter, ref.datasetType.name):
                continue

            display_string = f"{ref.datasetType.name}"
            plot_options[display_string] = ref

        # Use glob-style expressions instead of regexes
        # regex = fnmatch.translate(self.get_plot_filter())
        regex = fnmatch.translate("*Plot*")
        dataset_types = self.butler.registry.queryDatasetTypes(re.compile(regex))

        for dataset_type in dataset_types:
            if("visit" in dataset_type.dimensions):
                display_string = f"{dataset_type.name}"
                plot_options[display_string] = dataset_type
        return plot_options

    def select_plot_names(self, plot_names):
        self.selected_plot_names = plot_names
        self.notify_listeners()

    def get_selected_plot_names(self):
        return self.selected_plot_names

    def get_selected_plot_datarefs(self):
        refs = []
        for dataset_type in self.selected_plot_names:
            data_id = {"skymap": "hsc_rings_v1", "visit": self.visit,
                       "instrument": "HSC"}
            try:
                ref = self.butler.registry.queryDatasets(dataset_type, dataId=data_id,
                                                         collections=self.get_selected_collection(),
                                                         findFirst=True)
            except LookupError:
                continue

            ref_list = list(ref)
            if(len(ref_list) > 0):
                refs.append(ref_list[0])

        return refs

    def check_if_next_visit_exists(self):
        next_visit = self.visit + 1
        for dataset_type in self.selected_plot_names:
            data_id = {"skymap": "hsc_rings_v1", "visit": next_visit,
                       "instrument": "HSC"}
            try:
                result = self.butler.datasetExists(dataset_type, dataId=data_id,
                                                 collections=self.get_selected_collection())
            except LookupError:
                continue

            if(result):
                return True
        return False


