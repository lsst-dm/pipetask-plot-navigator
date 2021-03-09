FROM continuumio/miniconda3:4.9.2

RUN apt-get update && \
    apt-get install -y \
        build-essential \
    && rm -rf /var/lib/apt/lists/* 

RUN git clone https://github.com/lsst/sphgeom /lsst-sphgeom
WORKDIR /lsst-sphgeom
RUN pip install .
RUN git clone https://github.com/lsst/daf_butler /lsst-daf_butler
WORKDIR /lsst-daf_butler
RUN pip install .
WORKDIR /

RUN conda install -c holoviz panel=0.10.2 
RUN conda install bokeh=2.2.2
# RUN conda install -c dask-kubernetes -c conda-forge

COPY ./ /pipe-analysis-navigator/
WORKDIR /pipe-analysis-navigator

CMD panel serve dashboard_gen3.py --port 8080
