from pathlib import Path

filters = ["HSC-G", "HSC-R", "HSC-I", "HSC-Z", "HSC-Y", "NB0921"]
types = [
    "hist",
    "sky",
    "fpa",
    "psfMagHist",
    "quiver",
    "fit",
    "noFit",
    "noFitMagBins",
    "PerpSelections",
    "RhoStats",
]
category_path = Path(__file__).parent / "categories.csv"
plot_data_path = Path(__file__).parent / 'plot_data.hdf'

filters = ["HSC-G", "HSC-R", "HSC-I", "HSC-Z", "HSC-Y", "NB0921"]
datastyles = ["coadd", "visit"]
categories = ["astrometry", "photometry", "shape", "color"]
