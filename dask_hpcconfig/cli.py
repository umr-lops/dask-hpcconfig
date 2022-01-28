import asyncio
import enum
import pathlib
from contextlib import contextmanager
from functools import wraps

import rich.console
import typer
from distributed import Client
from rich.rule import Rule
from rich.table import Table
from tornado.ioloop import IOLoop

from . import available_clusters
from . import cluster as create_cluster

ClusterNames = enum.Enum("ClusterNames", {n: n for n in available_clusters()})
ClusterNames.__str__ = lambda x: x.name

# synchronize tornado and asyncio
loop = IOLoop.current()
asyncio.set_event_loop(loop.asyncio_loop)


@contextmanager
def no_op(*args, **kwargs):
    class Status:
        def __init__(self, *args, **kwargs):
            pass

        def update(self, *args, **kwargs):
            pass

        @property
        def status(self):
            return None

    try:
        yield Status(*args, **kwargs)
    finally:
        pass


class FakeConsole:
    def __init__(self):
        pass

    def __getattr__(self, name):
        return no_op


def format_client_versions(versions) -> Table:
    def format_environment(env):
        table = Table(box=None)
        table.add_column("")
        table.add_column("value")
        for p, v in sorted(env.items()):
            table.add_row(str(p), str(v))
        return table

    def format_system(system):
        # reformat to a table of package → system
        table = Table.grid(padding=1)
        table.add_column("environment", justify="center", style="bold")
        table.add_column("info")

        for name, env in system.items():
            subtable = format_environment(env)
            table.add_row(name, subtable)

        return table

    table = Table.grid(padding=1, pad_edge=True)
    table.add_column("system", no_wrap=True, justify="center", style="bold red")
    table.add_column("values")
    for section in ["client", "scheduler"]:
        data = versions.get(section)
        if data is None:
            continue

        subtable = format_system(data)
        table.add_row(section, subtable)

    return table


def async_command(app, *args, **kwargs):
    def decorator(async_func):
        @wraps(async_func)
        def sync_func(*_args, **_kwargs):
            return asyncio.run(async_func(*_args, **_kwargs))

        # register the synchronous function
        app.command(*args, **kwargs)(sync_func)

        # We return the async function unmodifed, so its library
        # functionality is preserved
        return async_func

    return decorator


typer.Typer.async_command = async_command


app = typer.Typer()


@app.async_command()
async def create(
    name: ClusterNames = typer.Argument(..., help="the name of the cluster definition"),
    workers: int = typer.Option(None, help="spawn N workers"),
    silent: bool = typer.Option(False, "--silent", help="don't print status messages"),
    pidfile: pathlib.Path = typer.Option(
        None, help="file to write the scheduler address to"
    ),
):
    """set up a new cluster instance"""
    if silent:
        console = FakeConsole()
    else:
        console = rich.console.Console()

    console.log(f"spawning a {name} cluster")
    cluster = await create_cluster(str(name), loop=loop, asynchronous=True)

    client = await Client(cluster, asynchronous=True)
    console.log(
        Rule("versions"),
        format_client_versions(await client.get_versions()),
        Rule(),
    )
    if pidfile is not None:
        pidfile.write_text(cluster.scheduler_address)
    console.log(f"scheduler address at: {cluster.scheduler_address}")
    console.log("dashboard at:", client.dashboard_link)

    if workers is not None:
        console.log(f"scaling to {workers} workers")
        await cluster.scale(workers)
        await client.wait_for_workers(1)

    with console.status("[bold blue]running until shutdown ... "):
        await cluster.scheduler.finished()
        console.log("cluster shut down")

    if pidfile is not None:
        pidfile.unlink(missing_ok=True)
        console.log("deleted scheduler address file")
    await client.close()
    console.log("disconnected client")


@app.async_command()
async def shutdown(
    address: str = typer.Argument(..., help="the scheduler address"),
    silent: bool = typer.Option(False, "--silent", help="don't print status updates"),
):
    """Shut down a running cluster"""
    if silent:
        console = FakeConsole()
    else:
        console = rich.console.Console()

    console.log(f"connecting to {address}")
    client = await Client(address, asynchronous=True)

    with console.status("[bold blue]cluster shutdown:[/]") as status:
        status.update(f"{status.status} [bold grey]shutting down the scheduler")
        await client.shutdown()
        status.update(f"{status.status} [bold grey]closing the client")
        await client.close()
    console.print("successfully shutdown the scheduler")


# for auto-documentation with `sphinx-click`
# once there is a `sphinx-typer` we should use that
click_app = typer.main.get_command(app)
