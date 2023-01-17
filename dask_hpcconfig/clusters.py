import dask

from .definitions import load_cluster_definitions
from .processors import expand_custom_cluster_settings, set_dashboard_link_jupyterhub
from .types import _cluster_type


def new_cluster(name, config, *, asynchronous=False, loop=None):
    type_name = config.get("type")
    if type_name is None:
        raise ValueError(f"cluster: configuration of {name} does not have a 'type' key")

    type_ = _cluster_type(type_name)
    cluster = type_(
        asynchronous=asynchronous,
        loop=loop,
        **{k.replace("-", "_"): v for k, v in config.items() if k != "type"},
    )

    return cluster


def inflate_mapping(mapping):
    def assign_nested(mapping, parts, value):
        cur = mapping
        for part in parts[:-1]:
            cur = cur.setdefault(part, {})

        cur[parts[-1]] = value

    new = {}
    for k, v in mapping.items():
        assign_nested(new, k.split("."), v)

    return new


def cluster(name, *, asynchronous=False, loop=None, **overrides):
    definitions = load_cluster_definitions()

    # find the requested configuration
    definition = definitions.get(name)
    if definition is None:
        raise ValueError(
            f"cluster: unknown configuration: {name!r}. Choose one of"
            f" {{{', '.join(map(repr, sorted(definitions.keys())))}}}."
        )

    # set the dashboard link if on jupyterhub
    definition = set_dashboard_link_jupyterhub(definition)

    # apply the overrides
    definition = dask.config.expand_environment_variables(
        dask.config.update(definition, inflate_mapping(overrides))
    )

    # convert special configuration settings
    definition = expand_custom_cluster_settings(definition)

    # split cluster from general config
    cluster_config = definition.get("cluster")
    if cluster_config is None:
        raise ValueError(
            f"cluster: malformed cluster definition of {name}: needs at least the 'cluster' key"
        )

    # instantiate cluster class
    cluster = new_cluster(name, cluster_config, asynchronous=asynchronous)

    # feed every other setting to `dask.config.merge` before passing it to `dask.config.set` (because
    # that replaces any top-level attributes)
    merged = dask.config.merge(
        dask.config.config, {k: v for k, v in definition.items() if k != "cluster"}
    )
    dask.config.set(merged)

    return cluster
