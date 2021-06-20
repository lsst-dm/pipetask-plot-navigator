import os
import logging

# Configure logging
log = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s [%(name)-12s] %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
log.addHandler(handler)
try:
    log.setLevel(os.environ['LOG_LEVEL'].upper())
except:
    log.setLevel('DEBUG')
    
from pathlib import Path
import re

import panel as pn
import param

from lsst.daf.butler import Butler

pn.extension()

default_repo = '/project/hsc/gen3repo/rc2w02_ssw03'

def find_types(registry, storageClassName='Plot'):
    types = []
    for t in registry.queryDatasetTypes():
        try:
            if t.storageClass.name == storageClassName:
                types.append(t)
        except:
            pass    

    return types
        
def find_refs(registry, collection, types):
    return list(registry.queryDatasets(types, collections=collection, findFirst=True))

def get_tracts(refs):
    tracts = list(set(r.dataId["tract"] for r in refs))
    tracts.sort()
    return tracts


class PlotExplorer(param.Parameterized):
        
    repo1 = param.String(default=default_repo)
    load1 = param.Action(lambda x: x.param.trigger('load1'), label='Load Butler 1')
    collection1 = param.ObjectSelector(default='', objects=[])

    repo2 = param.String(default=default_repo)
    load2 = param.Action(lambda x: x.param.trigger('load2'), label='Load Butler 2')
    collection2 = param.ObjectSelector(default='', objects=[])
        
    butler1 = param.ClassSelector(default=None, class_=Butler, precedence=-1)
    butler2 = param.ClassSelector(default=None, class_=Butler, precedence=-1)
        
    tract = param.ListSelector(objects=[])
    name_filter = param.String()
    plot_select = param.ListSelector(objects=[])
        
    plot_width = param.Integer(600, bounds=(300, 1200))
    ncols = param.Integer(2)
        
    debug = pn.widgets.StaticText(value=f"Status message.")
        
    plot_paths = param.Dict(precedence=-1)
    plot_paths2 = param.Dict(precedence=-1)
        
    def _load_butler(self, repo_path):
        log.debug(f'Loading butler repo from {repo_path}')
        try:
            butler = Butler(repo_path)
            return butler
        except Exception as e:
            self.debug.value = f'Failed to load Butler: {str(e)}'
            log.error(f'{str(e)}')
        
    @param.depends('load1', watch=True)
    def _update_butler1(self):
        self.butler1 = self._load_butler(self.repo1)
        if self.butler1 is not None:
            self.debug.value = f'Loaded Butler1 from {self.repo1}.'
            collections = list(self.butler1.registry.queryCollections())
            collections.sort()
            self.param.collection1.objects = collections

    @param.depends('load2', watch=True)
    def _update_butler2(self):
        self.butler2 = self._load_butler(self.repo2)
        if self.butler2 is not None:
            self.debug.value = f'Loaded Butler2 from {self.repo2}.'
            collections = list(self.butler2.registry.queryCollections())
            collections.sort()
            self.param.collection2.objects = collections

    @param.depends('collection1', 'collection2', watch=True)
    def _update_tract_select(self):
        registry = self.butler1.registry
        
        types = find_types(registry)

        if registry is not None:
            try:
                refs = find_refs(registry, self.collection1, types)
                if self.collection2:
                    refs2 = find_refs(registry, self.collection2, types)
                else:
                    refs2 = refs
                                
                self.param.tract.objects = list(set(get_tracts(refs)).intersection(set(get_tracts(refs2))))
                self.tract = []
            except:
                raise        
        
    @param.depends('tract', 'collection1', 'collection2', 'name_filter', watch=True)
    def _update_plot_names(self):
        
        registry = self.butler1.registry
        registry2 = self.butler2.registry if self.butler2 is not None else None
        
        plot_names = []
        plot_names2 = []
        plot_refs = []
        plot_refs2 = []
        types = find_types(registry)
        
        for tract in self.tract:
            refs = [
                ref
                for ref in registry.queryDatasets(
                    types,
                    collections=self.collection1,
                    findFirst=True,
                    dataId={"tract": tract},
                )
                if re.search(self.name_filter, ref.datasetType.name)
            ]
            names = [f"{p.datasetType.name} ({tract})" for p in refs]
            if registry2 is not None:
                refs2 = [
                    ref
                    for ref in registry2.queryDatasets(
                        types,
                        collections=self.collection2,
                        findFirst=True,
                        dataId={"tract": tract},
                    )
                    if re.search(self.name_filter, ref.datasetType.name)
                ]
                names2 = [f"{p.datasetType.name} ({tract})" for p in refs2]
            else:
                refs2 = refs
                names2 = names

            plot_refs.extend(refs)
            plot_refs2.extend(refs2)
            plot_names.extend(names)
            plot_names2.extend(names2)

        self.plot_paths = {
            name: self.butler1.getURI(ref, collections=self.collection1).path
            for name, ref in zip(plot_names, plot_refs)
        }

        if registry2 is not None:
            self.plot_paths2 = {
                name: self.butler2.getURI(ref, collections=self.collection2).path
                for name, ref in zip(plot_names2, plot_refs2)
            }

        plot_names = list(set(plot_names).intersection(plot_names2))
        plot_names.sort()
        
        self.param.plot_select.objects = plot_names     
        
    @param.depends('plot_select', 'butler1', 'butler2', 'collection1', 'collection2')
    def plots(self):
        if self.plot_select is not None:
            plot_list = [pn.pane.PNG(self.plot_paths[name], width=self.plot_width) 
                         for name in self.plot_select]
            plot_gbox = pn.GridBox(*plot_list, ncols=self.ncols)
                            
            if self.plot_paths2:
                plot_list2 = [pn.pane.PNG(self.plot_paths2[name], width=self.plot_width) 
                             for name in self.plot_select]
                plot_gbox2 = pn.GridBox(*plot_list2, ncols=self.ncols)
            else:
                plot_gbox2 = pn.GridBox([])

            return pn.Tabs(('collection 1', plot_gbox), ('collection 2', plot_gbox2))
        
    def panel(self):
        gspec = pn.GridSpec(sizing_mode="stretch_height", max_height=800)
        
        repo_collection_tabs = pn.Tabs(('Collection 1', pn.Column(self.param.repo1, self.param.load1, self.param.collection1)), 
                                       ('Collection 2', pn.Column(self.param.repo2, self.param.load2, self.param.collection2)))

        
        gspec[0:3, 0:2] = repo_collection_tabs
        
        gspec[3, 0:2] = self.param.tract
        gspec[4, 0:2] = self.param.name_filter
        gspec[5:12, 0:2] = self.param.plot_select
        
        gspec[0, 2:4] = self.debug
        gspec[1, 2] = pn.Param(self.param.plot_width, 
                               widgets={'plot_width': 
                                        {'widget_type': pn.widgets.IntInput,
                                        'start': 300,
                                        'end': 1200,
                                        'step': 50}})
        gspec[1, 3] = self.param.ncols
        gspec[2:, 2:4] = self.plots
        
        return gspec
    
explorer = PlotExplorer()
pn.Column(explorer.panel).servable()
