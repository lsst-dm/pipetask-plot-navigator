FROM ubuntu:18.04
ENV PATH="/root/miniconda3/bin:${PATH}"
ARG PATH="/root/miniconda3/bin:${PATH}"
RUN apt-get update

RUN apt-get install -y wget git build-essential && rm -rf /var/lib/apt/lists/* 

RUN wget \
    https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh \
    && mkdir /root/.conda \
    && bash Miniconda3-latest-Linux-x86_64.sh -b \
    && rm -f Miniconda3-latest-Linux-x86_64.sh 
RUN conda --version

# Install panel & dask

RUN conda install -c holoviz panel \
    && conda install dask-kubernetes -c conda-forge

# Clone dashboard repo

RUN git clone https://github.com/lsst/daf_butler \
    && cd daf_butler \
    && pip install . \
    && cd ..

ADD https://api.github.com/repos/timothydmorton/pipe-analysis-navigator/git/refs/heads/main version.json
RUN git clone -b main https://github.com/timothydmorton/pipe-analysis-navigator.git

# to mount volume: -v /project[original path]:/project [inside path]
# for ports, also at "docker run" time, then map ports, 55555:55555

# Launch dashboard

CMD cd pipe-analysis-navigator \
    && panel serve dashboard_gen3.py --port 55555


