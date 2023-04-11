FROM continuumio/miniconda3:22.11.1

RUN apt-get --allow-releaseinfo-change update && \
     rm -rf /var/lib/apt/lists/*


RUN conda config --add channels conda-forge 
RUN conda install panel=0.12 bokeh psycopg2=2 ipython

RUN pip install lsst-daf-butler[s3,postgres,gs]

RUN groupadd -g 4085 rubin_users
RUN useradd --create-home --shell /bin/bash worker --uid 1000 -G 4085
USER worker
WORKDIR /home/worker/

COPY --chown=worker:worker ./ app/
WORKDIR /home/worker/app

CMD panel serve dashboard_gen3.py --port 8080 --static-dirs assets=./assets
