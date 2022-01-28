cluster_types = {}


def register_cluster_type(name):
    def wrapper(func):
        cluster_types[name] = func

        return func

    return wrapper


@register_cluster_type("local")
def local_cluster():
    from distributed import LocalCluster

    return LocalCluster


@register_cluster_type("pbs")
def jobqueue_pbscluster():
    from dask_jobqueue import PBSCluster

    return PBSCluster


def _cluster_type(name):
    type_ = cluster_types.get(name)
    if type_ is None:
        raise ValueError(f"unknown cluster type: {name}")

    return type_()
