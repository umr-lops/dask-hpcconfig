import os

import dask


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
    if cluster_config is None:
        # invalid, but the error is raised later
        return definition

    memory = cluster_config.get("memory")
    if memory is None:
        # the memory has to be set
        return definition

    definition = definition.copy(deep=True)

    # pop because 'memory_limit' is a custom setting
    worker_memory = cluster_config.pop("worker_memory", None)
    processes = cluster_config.get("processes")

    memory_ = dask.utils.parse_bytes(memory)
    worker_memory_ = (
        dask.utils.parse_bytes(worker_memory) if worker_memory is not None else None
    )

    if worker_memory is not None and processes is None:
        # translate "memory_limit" to processes, and possibly adjust "memory"
        processes_ = memory_ // worker_memory_
        if processes_ == 0:
            raise ValueError(
                "invalid worker_memory:"
                f" per worker memory ({worker_memory}) must be smaller"
                f" or equal to the total memory ({memory})"
            )

        new_memory_ = processes_ * worker_memory_
    elif worker_memory is not None and processes is not None:
        processes_ = processes
        new_memory_ = processes_ * worker_memory_
    else:
        # nothing to do
        return definition

    new_memory = dask.utils.format_bytes(new_memory_)
    if new_memory_ > memory_:
        raise ValueError(
            f"the requested combination of 'worker_memory' ({worker_memory})"
            f" and 'processes' ({processes}) exceeds the total memory:"
            f" {new_memory} > {memory}"
        )

    new_settings = {"memory": new_memory, "processes": processes_}
    cluster_config = cluster_config | new_settings

    normalized = dask.config.canonical_name("resource_spec", cluster_config)
    if normalized in cluster_config:
        cluster_config[normalized] = update_resource_spec(
            cluster_config[normalized],
            {"mem": format_resource_size(new_memory_)},
        )

    definition = definition.copy()
    definition["cluster"] = cluster_config

    return definition
