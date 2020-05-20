FROM continuumio/miniconda3

RUN conda install -y -c conda-forge python-igraph
RUN conda install -y -c conda-forge igraph
RUN conda install -y -c conda-forge louvain
RUN conda install -y -c conda-forge leidenalg

RUN mkdir /tmp/hidef \
         && cd /tmp/hidef \
         && git clone -b cdhidef.0.2.0 --depth 1 https://github.com/coleslaw481/HiDeF \
         && cd HiDeF \
         && /opt/conda/bin/python setup.py bdist_wheel \
         && /opt/conda/bin/pip install dist/hidef*whl \
         && cd /tmp \
         && rm -rf /tmp/hidef

RUN mkdir /tmp/cdhidef
COPY dist/*.whl /tmp/cdhidef

RUN /opt/conda/bin/pip install /tmp/cdhidef/cdhidef*whl

RUN rm -rf /tmp/cdhidef

ENTRYPOINT ["/opt/conda/bin/cdhidefcmd.py"]
CMD ["--help"]
