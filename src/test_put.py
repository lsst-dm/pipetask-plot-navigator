#!/usr/bin/env python

import sys
import numpy as np
import matplotlib.pyplot as plt
import lsst.daf.butler as dafButler


def make_plot(plot_n):

    fig, ax = plt.subplots()
    x = np.random.randn(30)
    y = np.random.randn(30)

    ax.plot(x, y, 'o')
    ax.set_title("Plot {:d}".format(plot_n))
    ax.set_xlim(-2, 2)
    ax.set_ylim(-2, 2)
    return fig
    # plt.savefig("plot_{:03d}".format(plot_n))


if(len(sys.argv) > 2):
    dataset_type_name = sys.argv[2]
else:
    dataset_type_name = "visitPlot_demo"
print("Plot name ", dataset_type_name)

butler = dafButler.Butler(config="test_repo/butler.yaml", run="test_run")
butler.registry.registerCollection("test_run", type=dafButler.CollectionType.RUN)
try:
    butler.registry.insertDimensionData("visit_system", {"instrument": "HSC",
                                                         "id": 1,
                                                         "name": "default"})
except Exception as e:
    pass


visit_plot_type = dafButler.DatasetType(dataset_type_name, ("visit", "instrument"),
                                        storageClass="Plot",
                                        universe=butler.registry.dimensions)
butler.registry.registerDatasetType(visit_plot_type)

if(len(sys.argv) < 2):
    print("Must supply visit number as parameter")
    sys.exit(0)

visit = int(sys.argv[1])
print(f"Visit {visit:d}")
fig = make_plot(visit)
try:
    butler.registry.insertDimensionData("visit", {"instrument": "HSC", "id": visit,
                                                  "name": f"VISIT_{visit:07d}",
                                                  "physical_filter": "HSC-R",
                                                  "visit_system": 1})
except:
    pass

dataId = {"visit": visit, "instrument": "HSC"}
# {band, instrument, physical_filter, exposure
butler.put(fig, dataset_type_name, dataId)





