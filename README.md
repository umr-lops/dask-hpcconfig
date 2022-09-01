# dask-hpcconfig

To install, use
```bash
python -m pip install git+https://github.com/umr-lops/dask-hpcconfig.git#egg=dask-hpcconfig
```
or clone the source:
```bash
git clone https://github.com/umr-lops/dask-hpcconfig.git
cd dask-hpcconfig
```
and then install from there:
```bash
python -m pip install .
```
or as "editable":
```bash
python -m pip install -e .
```

## Usage
```python
import dask_hpcconfig
```

To list the available cluster definitions:
```python
dask_hpcconfig.print_clusters()
```
or, as a mapping of name to type:
```python
clusters = dask_hpcconfig.available_clusters()
```

To create a cluster, use:
```python
cluster = dask_hpcconfig.cluster(name)
```
where `name` is the name of one of the available clusters.

To override any particular setting:
For example on 'datarmor-local' to use only 7 workers for increasing memory size of each worker:
```python
overrides = {"cluster.n_workers": 7}
cluster = dask_hpcconfig.cluster("datarmor-local", **overrides)
```

For example on 'datarmor' to use only 7 workers for increasing memory size of each worker, and use 49 workers (i.e. 7 mpi_1 nodes) :
```python
overrides = {"cluster.cores": 7}
cluster = dask_hpcconfig.cluster("datarmor", **overrides)
cluster.scale(49)
```


`cluster` can then be used to create a `Client`:
```python
from distributed import Client

client = Client(cluster)
```
