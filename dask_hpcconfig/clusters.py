import os

import dask

from .definitions import load_cluster_definitions
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


def set_dashboard_link_jupyterhub(definition):
    # hack to work around a bug in dask-labextension
    jupyterhub_user = os.environ.get("JUPYTERHUB_USER")
    if jupyterhub_user:
        dashboard_link = "/user/{JUPYTERHUB_USER}/proxy/{port}/status"
        extra_configuration = {"distributed": {"dashboard": {"link": dashboard_link}}}
        definition = dask.config.update(definition, extra_configuration)

    return definition


def split_spec(spec, separators=[":", ","], key_value_sep="="):
    for sep in separators:
        settings_ = [setting.split("=") for setting in spec.split(sep)]
        if all(len(setting) == 2 for setting in settings_):
            return dict(settings_), sep

    raise ValueError(f"could not the detect settings separator in {spec!r}")


def join_spec(settings, sep, key_value_sep="="):
    return sep.join(key_value_sep.join(item) for item in settings.items())


def update_resource_spec(spec, new_values):
    settings, sep = split_spec(spec)
    updated = settings | {k: v for k, v in new_values.items() if k in settings}
    return join_spec(updated, sep=sep)


def format_resource_size(n):
    for prefix, k in (
        ("P", 2**50),
        ("T", 2**40),
        ("G", 2**30),
        ("M", 2**20),
        ("k", 2**10),
    ):
        if n >= k * 0.9:
            return f"{round(n / k)}{prefix}B"

    return f"{n}B"


def expand_custom_cluster_settings(definition):
    """
    compute the total resources

    The options to control resource usage are:
    - job memory (`memory`)
    - per worker memory (`memory_limit`)
    - number of workers (`processes`)

    Since `memory` has to always be specified as an upper limit, this leaves us with three
    combinations:
    - `memory` and `memory_limit`: compute processes and adjust `memory`
    - `memory` and `processes`: standard mode: just pass everything as is
    - `processes` and `memory_limit`: compute new memory

    These will fail if
    - `processes` would be 0
    - the computed `memory` would exceed the given maximum value
    """

    cluster_config = definition.get("cluster")
    if cluster is None:
        # invalid, but the error is raised later
        return definition

    memory = cluster_config.get("memory")
    if memory is None:
        # the memory has to be set
        return definition

    # pop because 'memory_limit' is a custom setting
    memory_limit = cluster_config.pop("memory_limit")
    processes = cluster_config.get("processes")

    memory_ = dask.utils.parse_bytes(memory)
    memory_limit_ = dask.utils.parse_bytes(memory_limit)

    if memory_limit is not None and processes is None:
        # translate "memory_limit" to processes, and possibly adjust "memory"
        processes_ = memory_ // memory_limit_
        if processes_ == 0:
            raise ValueError(
                "invalid memory_limit:"
                f" per worker memory ({memory_limit}) must be smaller"
                f" or equal to the total memory ({memory})"
            )

        new_memory_ = processes_ * memory_limit_
    elif memory_limit is not None and processes is not None:
        processes_ = processes
        new_memory_ = processes_ * memory_limit_
    else:
        # nothing to do
        return definition

    new_memory = dask.utils.format_bytes(new_memory_)
    if new_memory_ > memory_:
        raise ValueError(
            f"the requested combination of 'memory_limit' ({memory_limit})"
            f" and 'processes' ({processes}) exceeds the total memory:"
            f" {new_memory} > {memory}"
        )

    new_settings = {"memory": new_memory, "processes": processes_}
    cluster_config.update(new_settings)

    normalized = dask.config.canonical_name("resource_spec", cluster_config)
    if normalized in cluster_config:
        cluster_config[normalized] = update_resource_spec(
            cluster_config[normalized],
            {"mem": format_resource_size(new_memory_)},
        )

    definition["cluster"] = cluster_config

    return definition


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

    return definition

    # instantiate cluster class
    cluster = new_cluster(name, cluster_config, asynchronous=asynchronous)

    # feed every other setting to `dask.config.merge` before passing it to `dask.config.set` (because
    # that replaces any top-level attributes)
    merged = dask.config.merge(
        dask.config.config, {k: v for k, v in definition.items() if k != "cluster"}
    )
    dask.config.set(merged)

    return cluster
