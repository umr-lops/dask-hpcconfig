from dask_hpcconfig.clusters import cluster
from dask_hpcconfig.definitions import available_clusters, print_clusters
from dask_hpcconfig.types import register_cluster_type

try:
    import importlib.metadata

    __version__ = importlib.metadata.version("dask-hpcconfig")
except Exception:
    # local copy or not installed with setuptools
    # disable minimum version checks on downstream libraries
    __version__ = "999"


__all__ = ["cluster", "available_clusters", "print_clusters", "register_cluster_type"]
