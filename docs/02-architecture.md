# Milvus Architecture

This document explains the main components of Milvus and how they work together
in the standalone Docker Compose environment used by this project.

## Architecture Overview

Milvus is not only a process that stores vectors. It coordinates several
components to manage metadata, accept data, store vector files, build indexes,
and execute similarity searches.

This learning environment runs three main services:

- Milvus Standalone
- etcd
- MinIO

The standalone deployment is suitable for:

- Local development
- Learning
- Small demonstrations
- Functional testing
- Prototyping

It is not intended to represent a production cluster with independently scaled
Milvus components.

## Local Architecture

```text
                       Python application
                              |
                              | PyMilvus / gRPC
                              | Port 19530
                              v
                    +-------------------+
                    | Milvus Standalone |
                    +-------------------+
                       |             |
              metadata|             |vector and index files
                       v             v
                 +----------+   +----------+
                 |   etcd   |   |  MinIO   |
                 +----------+   +----------+
```

The Python examples communicate only with Milvus. They do not normally connect
directly to etcd or MinIO.

Milvus decides what metadata must be stored in etcd and what data files must be
stored in MinIO.

## Milvus Standalone

Milvus Standalone combines the major Milvus services inside one container.

Its responsibilities include:

- Accepting client connections
- Validating collection schemas
- Coordinating insert operations
- Managing query and search requests
- Creating and loading indexes
- Coordinating data persistence
- Communicating with etcd and MinIO
- Managing internal message flow

The Docker Compose service uses:

```yaml
image: milvusdb/milvus:v2.3.3
```

The container starts Milvus with:

```text
milvus run standalone
```

## Client Communication Port

Milvus exposes port `19530` for client operations.

PyMilvus connects to this port:

```python
connections.connect(
    alias="default",
    host="127.0.0.1",
    port="19530",
)
```

Operations sent through this connection include:

- Creating collections
- Inserting entities
- Creating indexes
- Loading collections
- Running vector searches
- Running scalar queries
- Deleting entities

## Health and Metrics Port

The standalone service also exposes port `9091`.

This project uses its health endpoint:

```bash
curl http://127.0.0.1:9091/healthz
```

A healthy service returns:

```text
OK
```

The health endpoint is useful for Docker health checks, monitoring, and
troubleshooting.

## etcd

etcd is a distributed key-value store. Milvus uses it primarily for metadata
and coordination.

Examples of information associated with Milvus metadata include:

- Collection definitions
- Field schemas
- Collection identifiers
- Partition information
- Segment metadata
- Index metadata
- Component registration
- Service coordination state

etcd does not normally store the large vector data files themselves.

In this project, etcd uses the following Docker image:

```yaml
image: quay.io/coreos/etcd:v3.5.5
```

Milvus accesses etcd through the internal Docker network:

```text
etcd:2379
```

The host machine does not need to expose the etcd port for the Python examples.

## MinIO

MinIO is an S3-compatible object storage service.

Milvus uses MinIO to store persistent binary objects such as:

- Insert logs
- Scalar-field data
- Vector-field data
- Statistics logs
- Delta logs related to deletions
- Index files
- Other segment-related objects

In this project, MinIO is available internally at:

```text
minio:9000
```

The MinIO API and web console are also exposed to the host:

```text
API:     http://127.0.0.1:9000
Console: http://127.0.0.1:9001
```

The Python examples do not upload vectors directly to MinIO. Data is sent to
Milvus, and Milvus writes the required persistent objects to MinIO.

## Message Storage

Milvus components exchange internal messages during insert and data-processing
operations.

This project uses:

```yaml
MQ_TYPE: rocksmq
```

Rocksmq is a local message-queue implementation suitable for a standalone
Milvus deployment.

Its local files are stored under the Milvus data directory. A distributed
production deployment may use a different message system, depending on the
Milvus version and architecture.

## Docker Network

Docker Compose creates a private network for the services.

Inside this network, containers use service names instead of host IP addresses:

```text
Milvus -> etcd:2379
Milvus -> minio:9000
```

From the host machine, PyMilvus connects through the published port:

```text
127.0.0.1:19530
```

The difference is important:

- Container-to-container traffic uses Docker service names.
- Host-to-container traffic uses published host ports.

## Persistent Volumes

Container files disappear when a container is recreated unless persistent
storage is mounted.

This project stores service data in:

```text
volumes/
├── etcd/
├── minio/
└── milvus/
```

The Docker Compose mappings are conceptually:

```text
./volumes/etcd   -> /etcd
./volumes/minio  -> /minio_data
./volumes/milvus -> /var/lib/milvus
```

The local `volumes/` directory is excluded from Git because it contains runtime
data rather than source code.

## What Is Stored Where?

| Component | Main responsibility | Example stored information |
|---|---|---|
| Milvus | Vector database engine | Runtime state and local message data |
| etcd | Metadata and coordination | Collections, schemas, segments, indexes |
| MinIO | Object storage | Vector data, scalar data, logs, index files |
| PyMilvus | Client library | Sends database operations to Milvus |

A consistent Milvus environment depends on the relationship among these
components. Copying only one data directory is generally not a complete backup.

## Insert Flow

When the Python application inserts entities, the simplified process is:

```text
Python application
        |
        | collection.insert(...)
        v
Milvus validates the schema and accepts the data
        |
        | internal message processing
        v
Milvus organizes data into segments
        |
        +----> metadata is recorded through etcd
        |
        +----> persistent data objects are written to MinIO
```

Calling:

```python
collection.flush()
```

asks Milvus to persist pending insert data so that it is no longer only part of
the active write process.

## Search Flow

A simplified vector-search flow is:

```text
Python query vector
        |
        v
Milvus Proxy
        |
        v
Query processing
        |
        +----> reads collection and segment metadata
        |
        +----> uses loaded vector data and indexes
        |
        v
Returns the nearest matching entities
```

A collection generally needs to be loaded before search:

```python
collection.load()
```

Loading prepares the collection's data and index structures for query
execution.

## Why Disk Space Matters

MinIO protects its storage backend when the available disk space becomes too
low.

If the disk reaches MinIO's minimum free-space threshold, write operations may
fail with an error similar to:

```text
Storage backend has reached its minimum free drive threshold
```

When this happens:

1. Milvus may accept the insert request initially.
2. The later flush operation attempts to write objects to MinIO.
3. MinIO rejects the write because free space is too low.
4. The Milvus flush fails.
5. The standalone process may stop, depending on the Milvus version.

For this reason, monitoring disk space is an important operational task:

```bash
df -h
```

## Service Dependencies

Milvus depends on both etcd and MinIO.

The expected startup order is:

1. Start etcd.
2. Start MinIO.
3. Wait until both services are healthy.
4. Start Milvus Standalone.
5. Connect with PyMilvus.

Docker Compose manages these services, but health checks should still be
verified:

```bash
docker compose ps
```

## Starting the Environment

Start all services using locally available images:

```bash
docker compose up -d --pull never
```

The `--pull never` option is used in this environment because access to the
external container registry may be restricted.

## Checking Service Status

Display the service state:

```bash
docker compose ps
```

Check Milvus health:

```bash
curl http://127.0.0.1:9091/healthz
```

Check recent logs:

```bash
docker compose logs --tail=100 standalone
docker compose logs --tail=100 etcd
docker compose logs --tail=100 minio
```

## Stopping the Environment

Stop the containers while preserving their data:

```bash
docker compose stop
```

Start the existing containers again:

```bash
docker compose start
```

Stop and remove the containers and network while preserving bind-mounted data:

```bash
docker compose down
```

Do not add the `-v` option unless volume deletion is explicitly intended.

## Standalone Versus Distributed Deployment

A standalone deployment runs the main Milvus components together and is easier
to operate.

A distributed deployment separates services so that they can be scaled and
managed independently.

| Standalone | Distributed |
|---|---|
| Easier to install | More operationally complex |
| Suitable for learning | Suitable for large workloads |
| Limited independent scaling | Components can scale independently |
| Fewer containers | Multiple service instances |
| Good for local development | Designed for production clusters |

## Failure Scenarios

Common architecture-related failures include:

### etcd is unavailable

Possible effects:

- Collection metadata cannot be read
- Components cannot coordinate
- Milvus may fail during startup

### MinIO is unavailable

Possible effects:

- Insert flush operations fail
- Segment files cannot be read
- Index files cannot be stored or loaded

### Milvus is unavailable

Possible effects:

- PyMilvus cannot connect to port `19530`
- Collection, insert, query, and search operations fail

### Disk space is exhausted

Possible effects:

- MinIO refuses new objects
- Flush operations fail
- Milvus may exit
- Data may remain incomplete or uncertain

## Key Operational Principle

Milvus, etcd, and MinIO form one logical storage system.

For reliable operation:

- Keep all services healthy.
- Preserve all persistent directories.
- Monitor disk space.
- Use compatible component versions.
- Back up metadata and object data consistently.
- Avoid manually modifying files inside the volume directories.

## Next Step

The next document, `03-collections-and-schema.md`, explains how collections,
fields, primary keys, and vector dimensions are defined.
