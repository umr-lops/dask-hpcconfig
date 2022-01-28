dask-hpcconfig: database of cluster configurations
==================================================

`dask`_, `distributed`_ and `deployment packages`_ like
`dask-jobqueue`_ or `dask-kubernetes`_ have a dazzling amount of
settings allowing to fine-tune a cluster.

However, as useful as that is for experts, new users easily get
confused by the steps necessary to create a cluster. For `dask-jobqueue`_:

1. copy this configuration file to that directory and remember the
   name
2. install the appropriate deployment package
3. instantiate the appropriate class using that name,
   e.g. :py:class:`dask_jobqueue.PBSCluster`

``dask-hpcconfig`` aims to make this much easier by providing a
unified API and by shipping a pre-configured set of cluster
definitions. This will change the list above to:

1. install the appropriate deployment package
2. call :py:func:`dask_hpcconfig.cluster` with the desired cluster
   configuration name

where :py:func:`dask_hpcconfig.cluster` will tell the name of the
package to install if it is still missing.

.. _dask: https://dask.org
.. _distributed: https://distributed.dask.org
.. _deployment packages: https://docs.dask.org/en/latest/ecosystem.html#deploying-dask
.. _dask-jobqueue: https://jobqueue.dask.org
.. _dask-kubernetes: https://kubernetes.dask.org

.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: Getting started

   getting-started/installing
   getting-started/quickstart

.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: User guide

   user-guide/programmatic
   user-guide/cli

.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: Reference

   reference/api
   reference/cli
