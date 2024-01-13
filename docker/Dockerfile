FROM continuumio/miniconda3

RUN apt-get --allow-releaseinfo-change update
RUN apt-get install -y build-essential

RUN conda install -y -c conda-forge python-igraph
RUN conda install -y -c conda-forge igraph
RUN conda install -y -c conda-forge louvain
RUN conda install -y -c conda-forge leidenalg

RUN /opt/conda/bin/pip install hidef==1.1.5a2
RUN /opt/conda/bin/pip install ndex2>=3.7.0

RUN mkdir /tmp/cdhidef
COPY dist/*.whl /tmp/cdhidef

RUN /opt/conda/bin/pip install /tmp/cdhidef/cdhidef*whl

RUN rm -rf /tmp/cdhidef

ENTRYPOINT ["/opt/conda/bin/cdhidefcmd.py"]
CMD ["--help"]
