# Troubleshooting a Stuck Milvus Collection Load

This guide explains how to diagnose a Milvus collection that remains in a
loading state or causes `collection.load()` to wait for a long time.

## What Does `collection.load()` Do?

Milvus cannot perform vector search directly from persistent object storage.

Before searching, Milvus must load the required collection data and index into
the QueryNode memory. In standalone mode, the required Milvus components run
inside the same Milvus container, but the loading process still depends on:

- Milvus metadata stored through etcd
- Insert logs and index files stored in MinIO
- Healthy internal Milvus components
- Available memory
- Available disk space
- A valid and complete vector index
- Compatible metadata and storage data

Example:

```python
from pymilvus import Collection

collection = Collection("learning_vectors")
collection.load()
```

If one of the required components is unhealthy or inconsistent, the call may
take a long time, retry repeatedly, or fail.

## Common Symptoms

A loading problem may appear as:

* `collection.load()` does not return
* A search request waits indefinitely
* The collection remains partially loaded
* Milvus repeatedly logs component connection errors
* The Python client reports a timeout
* Milvus restarts while loading
* Search fails after a restore
* QueryNode cannot read index or insert-log files

## Step 1: Check Available Disk Space

Check filesystem usage:

```bash
df -h
```

MinIO requires sufficient free disk space. When the disk is almost full, MinIO
may reject writes with an error similar to:

```text
Storage backend has reached its minimum free drive threshold.
```

Milvus may then fail to flush data or create complete persistent files.
Incomplete operations can later affect loading.

Also check inode usage:

```bash
df -i
```

A filesystem may have free bytes but no available inodes.

## Step 2: Check Container Status

Run:

```bash
docker compose ps
```

All required services should be running:

* `milvus-etcd`
* `milvus-minio`
* `milvus-standalone`

If the Milvus container has exited, inspect its exit code:

```bash
docker inspect milvus-standalone \
  --format 'status={{.State.Status}} exit_code={{.State.ExitCode}}'
```

## Step 3: Check the Milvus Health Endpoint

Run:

```bash
curl -i http://127.0.0.1:9091/healthz
```

A healthy response should contain:

```text
HTTP/1.1 200 OK

OK
```

A successful Docker container start does not always mean that Milvus is ready
to accept searches. Wait for the health check before running Python examples.

## Step 4: Inspect Milvus Logs

Display recent logs:

```bash
docker compose logs --tail=300 standalone
```

Filter important messages:

```bash
docker compose logs standalone 2>&1 \
  | grep -iE 'load|querynode|error|fatal|panic|failed|timeout|minio|etcd'
```

Look for:

* QueryNode registration problems
* RootCoord or DataCoord connection failures
* MinIO read failures
* Missing objects
* Index-loading failures
* Out-of-memory errors
* Context cancellation
* Repeated retries
* Panic messages

Do not rely only on the final error line. Earlier log entries often contain the
original cause.

## Step 5: Inspect MinIO Logs

Run:

```bash
docker compose logs --tail=300 minio
```

Search for storage errors:

```bash
docker compose logs minio 2>&1 \
  | grep -iE 'error|disk|drive|threshold|denied|timeout'
```

Verify that the local MinIO data directory exists:

```bash
ls -ld volumes/minio
```

Milvus metadata may reference objects that MinIO cannot read if:

* MinIO data was deleted
* The wrong data directory was mounted
* Only etcd was restored
* Object data belongs to a different backup
* Permissions prevent MinIO from reading files

## Step 6: Inspect etcd Logs

Run:

```bash
docker compose logs --tail=300 etcd
```

Search for important messages:

```bash
docker compose logs etcd 2>&1 \
  | grep -iE 'error|corrupt|timeout|unhealthy|space|quota'
```

Check the etcd container health:

```bash
docker inspect milvus-etcd \
  --format '{{json .State.Health}}'
```

etcd contains Milvus metadata and coordination state. If etcd metadata does not
match the MinIO and Milvus data, a collection may exist in metadata but its
segments or indexes may not be available.

## Step 7: Check Collection and Loading State

Use PyMilvus to list collections:

```bash
python -c "
from pymilvus import connections, utility
connections.connect(host='127.0.0.1', port='19530')
print(utility.list_collections())
connections.disconnect('default')
"
```

Check the loading state:

```bash
python -c "
from pymilvus import connections, utility
connections.connect(host='127.0.0.1', port='19530')
print(utility.load_state('learning_vectors'))
connections.disconnect('default')
"
```

Check collection information:

```bash
python -c "
from pymilvus import Collection, connections
connections.connect(host='127.0.0.1', port='19530')
collection = Collection('learning_vectors')
print('Entities:', collection.num_entities)
print('Indexes:', [index.params for index in collection.indexes])
connections.disconnect('default')
"
```

Replace `learning_vectors` with the required collection name.

## Step 8: Verify That an Index Exists

Vector searches usually require an index.

Run the index example:

```bash
python examples/04_create_index.py
```

The learning project uses:

```text
Index type: HNSW
Metric type: COSINE
```

If index creation previously failed because of low disk space or a Milvus
crash, inspect the logs before attempting to load the collection again.

## Step 9: Check Memory and Swap

Run:

```bash
free -h
```

Check container memory usage:

```bash
docker stats --no-stream
```

Loading large collections and indexes requires memory. If the operating system
kills Milvus because of memory pressure, inspect kernel messages:

```bash
sudo dmesg -T | grep -iE 'out of memory|oom|killed process'
```

For large production collections, avoid loading everything when the available
memory is insufficient. Consider partition-based loading and capacity
planning.

## Step 10: Restart Services Safely

If storage and metadata are healthy, restart the environment:

```bash
docker compose restart
```

Wait for the services:

```bash
docker compose ps
curl -f http://127.0.0.1:9091/healthz
```

Then test the connection:

```bash
python examples/01_connect.py
```

Finally retry the search:

```bash
python examples/05_search_vectors.py
```

Restarting may recover a transient component failure, but it does not repair
missing data or an inconsistent restore.

## Releasing a Loaded Collection

When an application no longer needs a collection in memory, release it:

```python
collection.release()
```

This releases QueryNode memory associated with the collection. It does not
delete the collection or its persistent data.

## Loading With a Timeout

For operational tools, use a finite timeout so that a problem does not appear
as an endless wait:

```python
collection.load(timeout=60)
```

The correct timeout depends on collection size, index size, storage speed, and
available resources. A timeout is a diagnostic and operational safeguard; it
does not solve the underlying loading problem.

## Restore-Related Loading Problems

A Milvus collection depends on a consistent set of data:

* etcd metadata
* MinIO objects
* Milvus local data and message-queue state
* Compatible Milvus configuration and versions

Restoring only etcd may make the collection names visible while the referenced
objects are missing from MinIO.

Restoring only MinIO does not restore Milvus metadata.

A reliable restore must use components from the same backup point and follow a
tested recovery procedure. Stop writes or use an officially supported backup
workflow to achieve consistency.

After a restore, verify:

1. All containers use the expected versions.
2. Volume mount paths are correct.
3. etcd and MinIO data come from the same backup.
4. Milvus becomes healthy.
5. Collections are listed.
6. Entity counts are reasonable.
7. Index metadata exists.
8. Collections can load.
9. Known vectors return expected search results.

## When Recreating a Collection Is Acceptable

For this learning repository, the demo collections contain disposable data.
If a demo collection becomes inconsistent, it can be recreated and the
examples can be rerun.

Do not apply this approach to production data.

Before dropping any real collection:

* Confirm the exact collection name.
* Confirm that the data is disposable or backed up.
* Verify that the backup can be restored.
* Record the current schema and index configuration.
* Obtain the required operational approval.

## Quick Diagnostic Checklist

Use this order:

1. `df -h`
2. `df -i`
3. `free -h`
4. `docker compose ps`
5. Milvus health endpoint
6. Milvus logs
7. MinIO logs
8. etcd logs
9. Collection loading state
10. Collection indexes
11. Volume mount paths
12. Restore consistency
13. Controlled restart
14. Search verification

The most important rule is to identify the underlying storage, metadata,
resource, or version problem before deleting data or recreating a collection.
