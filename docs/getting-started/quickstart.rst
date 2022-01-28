Quickstart
==========

.. ipython::

   In [1]: import distributed
      ...: import dask_hpcconfig

Starting a cluster is easy:

.. ipython::

   In [2]: # find the available clusters
      ...: dask_hpcconfig.print_clusters()

   In [3]: # as an example, let's choose 'local'
      ...: cluster = dask_hpcconfig.cluster("local")

and with that, we have a running cluster. Now we can do the usual:
spawn workers, create a client and compute something.


.. ipython::

   In [4]: # spawn 4 workers
      ...: cluster.scale(n=4)

   In [5]: # create the client
      ...: client = distributed.Client(cluster)

   In [6]: import dask.array as da
      ...:
      ...: arr = da.ones(shape=(1000, 1000), chunks=(10, 10))
      ...: arr.sum().compute()

If we have a process that needs to be pointed at the scheduler of a
running cluster, we can do the same using the CLI:

.. code:: bash

    $ dask-hpcconfig create local --workers 14

This will create the cluster and keep it running until either the
scheduler is shut down or the process is terminated (using a keyboard interrupt, for example).
