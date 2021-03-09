from dask.distributed import Client, LocalCluster
import dask.array as da

cluster = LocalCluster()
client = Client(cluster)

print(client)

array = da.ones((1000, 1000, 1000))
print(array.mean().compute())

