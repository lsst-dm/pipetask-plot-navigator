FROM daskdev/dask

RUN pip install panel

# Clone dashboard repo
ADD https://api.github.com/repos/timothydmorton/pipe-analysis-navigator/git/refs/heads/main version.json
RUN git clone -b dask-test https://github.com/timothydmorton/pipe-analysis-navigator.git

# to mount volume: -v /project[original path]:/project [inside path]
# for ports, also at "docker run" time, then map ports, 55555:55555

# Launch dashboard

# CMD cd pipe-analysis-navigator \
#    && panel serve dashboard_gen3.py --port 55555

CMD cd pipe-analysis-navigator \
    && python test_dask.py

