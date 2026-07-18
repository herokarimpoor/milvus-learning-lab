# Common Milvus Errors and Solutions

This guide documents common problems that may occur while running Milvus,
Docker Compose, and PyMilvus.

The examples are based on the local environment used in this repository:

- Milvus 2.3.3
- PyMilvus 2.3.7
- Python 3.10
- Docker Compose
- etcd
- MinIO

## 1. Connection Refused on Port 19530

Example error:

```text
failed to connect to all addresses
Connection refused
```

This error means that PyMilvus cannot connect to the Milvus gRPC service.

Check the containers:

```bash
docker compose ps
```

Check whether port `19530` is listening:

```bash
ss -lntp | grep 19530
```

Check the Milvus health endpoint:

```bash
curl -i http://127.0.0.1:9091/healthz
```

A healthy response should contain:

```text
HTTP/1.1 200 OK

OK
```

If Milvus is not running, inspect its logs:

```bash
docker compose logs --tail=200 standalone
```

## 2. Docker Registry Access Denied

Example errors:

```text
pull access denied
403 Forbidden
RBAC: access denied
```

These errors occur when Docker cannot download an image from Docker Hub,
Quay, or another registry.

Test Docker Hub access:

```bash
curl -I https://registry-1.docker.io/v2/
```

List locally available images:

```bash
docker images
```

If registry access is blocked but the required images already exist locally,
start the services without pulling newer images:

```bash
docker compose up -d --pull never
```

The image tags in `docker-compose.yml` must exactly match locally available
image tags.

Check a local image:

```bash
docker image inspect milvusdb/milvus:v2.3.3
```

Do not use `latest` automatically for every service in a production
environment. Explicit and tested versions are safer.

## 3. Milvus Exits Immediately

Check the service state:

```bash
docker compose ps
```

Then inspect the logs:

```bash
docker compose logs --tail=300 standalone
```

Search for important error messages:

```bash
docker compose logs standalone 2>&1 \
  | grep -iE 'error|fatal|panic|failed|unsupported'
```

Common causes include:

* Incompatible service versions
* An unsupported message-queue configuration
* etcd not being healthy
* MinIO not being healthy
* Insufficient disk space
* Incorrect volume permissions
* Corrupted or incompatible persisted data

## 4. Invalid Message Queue Type

Example error:

```text
panic: mq type woodpecker is invalid
```

This can happen when a Docker Compose configuration generated for a newer
Milvus version is used with an older Milvus image.

Milvus 2.3.3 can use Rocksmq in standalone mode:

```yaml
environment:
  MQ_TYPE: rocksmq
```

After changing the configuration, validate it:

```bash
docker compose config --quiet
```

Then restart the services:

```bash
docker compose down
docker compose up -d --pull never
```

Service configuration and container image versions must remain compatible.

## 5. MinIO Minimum Free Drive Threshold

Example error:

```text
Storage backend has reached its minimum free drive threshold.
Please delete a few objects to proceed.
```

MinIO prevents new writes when the filesystem has too little free space.
Milvus may fail during `insert()`, `flush()`, index creation, or collection
loading because Milvus stores persistent data in object storage.

Check disk usage:

```bash
df -h
```

Check the largest top-level directories:

```bash
sudo du -xhd1 / 2>/dev/null | sort -h
```

Check the current user's largest directories:

```bash
du -xhd1 "$HOME" 2>/dev/null | sort -h
```

Check Docker storage usage:

```bash
docker system df
```

Free disk space carefully, then restart the affected services:

```bash
docker compose restart minio standalone
```

Confirm health before running Python examples again:

```bash
curl -f http://127.0.0.1:9091/healthz
```

Do not delete Docker volumes or local Milvus data unless the data is
disposable or a verified backup exists.

## 6. PyMilvus Cannot Import `pkg_resources`

Example error:

```text
ModuleNotFoundError: No module named 'pkg_resources'
```

Older PyMilvus versions use `pkg_resources`, which is provided by compatible
Setuptools releases.

This repository pins Setuptools:

```text
setuptools==80.9.0
```

Install the project dependencies:

```bash
python -m pip install -r requirements.txt
```

Verify the import:

```bash
python -c "import pkg_resources; print('pkg_resources: OK')"
```

A deprecation warning may still appear. The warning does not prevent
PyMilvus 2.3.7 from working.

## 7. Marshmallow Compatibility Error

Example error:

```text
AttributeError: module 'marshmallow' has no attribute '__version_info__'
```

PyMilvus 2.3.7 depends on an older environment stack that is not compatible
with Marshmallow 4.

This repository pins:

```text
marshmallow==3.26.1
```

Reinstall the dependencies:

```bash
python -m pip install -r requirements.txt
python -m pip check
```

## 8. Client and Server Version Compatibility

The client and server should use compatible versions.

This repository uses:

```text
Milvus:   2.3.3
PyMilvus: 2.3.7
```

Check the Python client:

```bash
python -c "import pymilvus; print(pymilvus.__version__)"
```

Check the server through PyMilvus:

```bash
python examples/01_connect.py
```

Using a much newer client with an older server can introduce API,
dependency, or behavior differences.

## 9. Collection Does Not Exist

Example error:

```text
Collection 'learning_vectors' does not exist.
```

Create the collection first:

```bash
python examples/02_create_collection.py
```

Then insert the sample data:

```bash
python examples/03_insert_vectors.py
```

The examples should normally be executed in numerical order.

## 10. Collection Contains No Data

Vector search requires stored entities.

Check the collection by running:

```bash
python examples/03_insert_vectors.py
```

If the collection is empty, the script inserts the sample vectors.

If some records were previously deleted, the insertion script may skip
insertion because the collection is not completely empty. For a clean
learning run, use a separate reset procedure or recreate only the disposable
demo collection.

Never drop a production collection to reset a tutorial.

## 11. Duplicate Primary Keys

The sample collection uses manually assigned primary keys:

```text
1, 2, 3
```

Inserting the same identifiers repeatedly can cause duplicate records or
unexpected results, depending on the workflow.

The insertion example checks whether the collection already contains data and
skips repeated insertion.

For production systems, define a clear identifier strategy:

* Application-generated UUID
* Database-generated identifier
* Milvus automatic ID
* Stable external business identifier

## 12. Vector Dimension Mismatch

Example error:

```text
the length of a float vector does not match the schema dimension
```

A query or inserted vector must have exactly the same dimension as the vector
field schema.

The learning collection uses:

```text
dimension = 4
```

The face demonstration uses:

```text
dimension = 512
```

Check a vector dimension in Python:

```python
print(len(vector))
```

A 512-dimensional embedding cannot be inserted into a 4-dimensional vector
field.

## 13. Metric Type Mismatch

The metric used for searching should match the metric used by the vector
index.

This repository uses:

```text
COSINE
```

Use the same metric in both index and search configurations:

```python
"metric_type": "COSINE"
```

Mixing `COSINE`, `L2`, and `IP` without understanding their score semantics
can produce incorrect interpretation of results.

## 14. Port Already in Use

The standalone environment uses these host ports:

| Port    | Service                   |
| ------- | ------------------------- |
| `19530` | Milvus gRPC               |
| `9091`  | Milvus health and metrics |
| `9000`  | MinIO API                 |
| `9001`  | MinIO console             |

Check them before starting Docker Compose:

```bash
sudo ss -lntp | grep -E ':(19530|9091|9000|9001)\b'
```

Stop the conflicting service or change the host-side port mapping.

## 15. Docker Volume Permission Problems

Check the configured mounts:

```bash
docker inspect milvus-standalone \
  --format '{{range .Mounts}}{{println .Source "->" .Destination}}{{end}}'
```

Inspect local directories:

```bash
ls -ld volumes volumes/*
```

Avoid changing permissions recursively without identifying which container
user requires access. Broad commands such as `chmod -R 777` are unsafe and
should not be used as a default solution.

## Recommended Diagnostic Order

When an example fails, check the system in this order:

1. Verify available disk space with `df -h`.
2. Check container status with `docker compose ps`.
3. Check the Milvus health endpoint.
4. Inspect Milvus, MinIO, and etcd logs.
5. Verify ports and volume mounts.
6. Verify Python dependency versions.
7. Verify the collection schema and vector dimension.
8. Retry the smallest relevant example.
