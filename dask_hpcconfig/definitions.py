import functools
import importlib.resources

import yaml


@functools.lru_cache(maxsize=1)
def _load_cluster_definitions(f):
    return yaml.safe_load(f)


def load_cluster_definitions():
    f = importlib.resources.open_text("dask_hpcconfig", "clusters.yaml")
    return _load_cluster_definitions(f)


def available_clusters():
    """list the available cluster configuration names"""
    definitions = load_cluster_definitions()
    clusters = {n: v.get("cluster", {}).get("type") for n, v in definitions.items()}

    return clusters


def print_clusters():
    """print all available clusters and their type"""
    clusters = available_clusters()
    formatted = [f"{n}: {t}" for n, t in clusters.items()]

    print("Available clusters:", *formatted, sep="\n • ")
