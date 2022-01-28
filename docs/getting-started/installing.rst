Installing
==========
``dask-hpcconfig`` can be installed from github:

.. code:: bash

    python -m pip install git+https://github.com/umr-lops/dask-hpcconfig.git#egg=dask-hpcconfig

or by cloning the repository:

.. code:: bash

    git clone https://github.com/umr-lops/dask-hpcconfig.git
    cd dask-hpcconfig
    # if a specific version is desired
    git checkout <tag>  # see `git tag` for a list of available tags
    python -m pip install .

It has a few optional dependencies:

- `dask-jobqueue`_ for the pbs clusters
- `typer`_ and `rich`_ for the cli

.. _dask-jobqueue: https://github.com/dask/dask-jobqueue
.. _typer: https://github.com/tiangolo/typer
.. _rich: https://github.com/willmcgugan/rich
