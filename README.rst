===================================================
Community Detection HiDeF
===================================================

This repository creates a CDAPS compatible community detection Docker image using HiDeF `(Preprint) <https://doi.org/10.1101/2020.06.16.151555>`_
packaged from https://github.com/fanzheng10/HiDeF

Dependencies
------------

* `Docker <https://www.docker.com/>`_
* `make <https://www.gnu.org/software/make/>`_ (to build)
* Python (to build)

Direct invocation
------------------

Version `0.2.1` can be directly pulled from `Dockerhub <https://hub.docker.com/>`_ with this command:

.. code-block::

   docker pull coleslawndex/cdhidef:0.2.1

Building
--------

.. code-block::

   git clone https://github.com/idekerlab/cdhidef
   cd cdhidef
   make dockerbuild

Run **make** command with no arguments to see other build/deploy options including creation of Docker image

.. code-block::

   make

Output:

.. code-block::

   clean                remove all build, test, coverage and Python artifacts
   clean-build          remove build artifacts
   clean-pyc            remove Python file artifacts
   clean-test           remove test and coverage artifacts
   lint                 check style with flake8
   test                 run tests quickly with the default Python
   test-all             run tests on every Python version with tox
   coverage             check code coverage quickly with the default Python
   docs                 generate Sphinx HTML documentation, including API docs
   servedocs            compile the docs watching for changes
   testrelease          package and upload a TEST release
   release              package and upload a release
   dist                 builds source and wheel package
   install              install the package to the active Python's site-packages
   dockerbuild          build docker image and store in local repository
   dockerpush           push image to dockerhub


Usage
-----

.. code-block::

   docker run -v coleslawndex/cdhidef:0.2.1 -h


Credits
---------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
