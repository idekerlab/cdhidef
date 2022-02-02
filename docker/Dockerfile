FROM continuumio/miniconda3

RUN conda install -y -c conda-forge python-igraph
RUN conda install -y -c conda-forge igraph
RUN conda install -y -c conda-forge louvain
RUN conda install -y -c conda-forge leidenalg

RUN /opt/conda/bin/pip install hidef==1.1.3

RUN mkdir /tmp/cdhidef
COPY dist/*.whl /tmp/cdhidef

RUN /opt/conda/bin/pip install /tmp/cdhidef/cdhidef*whl

RUN rm -rf /tmp/cdhidef

ENTRYPOINT ["/opt/conda/bin/cdhidefcmd.py"]
CMD ["--help"]
