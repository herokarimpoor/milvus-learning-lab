# Milvus Backup and Restore

This document explains the basic backup and restore principles for the
standalone Milvus environment used in this project.

A Milvus backup is not only a copy of one directory. Milvus relies on multiple
storage components that must remain consistent with each other.

## Important Warning

Backup and restore operations can cause data loss when performed incorrectly.

Before restoring:

- Confirm the backup path.
- Confirm the Milvus version.
- Stop all related services.
- Preserve the current data before replacing it.
- Test the procedure with non-production data first.
- Never restore unrelated etcd and MinIO data together.

The commands in this document are intended for this learning environment.

## What Must Be Backed Up?

This project stores data in three directories:

```text
volumes/
├── etcd/
├── minio/
└── milvus/
```

Each directory has a different role.

| Directory | Main content |
|---|---|
| `volumes/etcd` | Collections, schemas, segment metadata, index metadata |
| `volumes/minio` | Vector data, scalar data, insert logs, index files |
| `volumes/milvus` | Local Milvus and Rocksmq runtime data |

A reliable standalone backup should preserve all three directories from the
same point in time.

## Why One Directory Is Not Enough

### Backing up only etcd

etcd may contain the collection schema and segment metadata, but the referenced
vector and index objects in MinIO may be missing.

Possible result:

- Collections appear to exist.
- Data loading fails.
- Search fails.
- Segments reference missing objects.

### Backing up only MinIO

MinIO may contain vector files and index files, but Milvus may not have the
metadata required to interpret them.

Possible result:

- Objects exist in storage.
- Collections are not registered.
- Segment relationships are unknown.
- Stored objects cannot be used correctly.

### Backing up only the Milvus directory

The local directory may contain Rocksmq and runtime files, but it does not
replace the metadata in etcd or the persistent objects in MinIO.

## Backup Consistency

A consistent backup represents all components at approximately the same logical
point in time.

If data continues to be inserted while the directories are copied, the backup
may contain:

- New etcd metadata with old MinIO objects
- New MinIO objects with old metadata
- Incomplete message data
- Partially completed flush operations
- Incomplete index files

For this local learning environment, the simplest reliable method is a cold
backup.

## What Is a Cold Backup?

A cold backup is created while the services are stopped.

The basic procedure is:

1. Stop applications that write to Milvus.
2. Flush pending data.
3. Stop Milvus, etcd, and MinIO.
4. Copy all persistent directories.
5. Verify the backup archive.
6. Start the services again.

Advantages:

- Simple
- Easy to understand
- Lower risk of component inconsistency
- Appropriate for a local standalone environment

Disadvantages:

- Requires downtime
- Not ideal for large production systems
- Service is unavailable during backup

## Preparing for Backup

Go to the project directory:

```bash
cd ~/Documents/milvus-learning-lab
```

Check the services:

```bash
docker compose ps
```

Check available disk space:

```bash
df -h
```

A backup requires enough space for the archive and temporary operations.

## Flushing Collections

Applications should flush pending writes before the services are stopped.

Example:

```python
from pymilvus import Collection, connections

connections.connect(
    alias="default",
    host="127.0.0.1",
    port="19530",
)

collection = Collection("learning_vectors")
collection.flush()

connections.disconnect("default")
```

A successful flush helps ensure pending insert data is persisted.

A flush does not replace a complete backup.

## Stopping the Services

Stop all services cleanly:

```bash
docker compose stop
```

Verify that they are stopped:

```bash
docker compose ps
```

Do not copy the active storage directories while Milvus is still writing to
them when using the cold-backup method.

## Creating a Backup Directory

Create a directory for local backup archives:

```bash
mkdir -p backups
```

The `backups/` directory should be excluded from Git because backup archives may
be large and may contain application data.

A timestamp can be generated with:

```bash
date '+%Y-%m-%d_%H-%M-%S'
```

## Creating a Compressed Archive

After the services are stopped, create an archive:

```bash
tar -czf backups/milvus-standalone-backup.tar.gz volumes
```

This archive contains:

```text
volumes/etcd
volumes/minio
volumes/milvus
```

For repeated backups, use a unique timestamp in the filename:

```bash
tar -czf "backups/milvus-standalone-$(date '+%Y-%m-%d_%H-%M-%S').tar.gz" volumes
```

## Verifying the Archive

List the archive:

```bash
ls -lh backups
```

Inspect its content without extracting it:

```bash
tar -tzf backups/milvus-standalone-backup.tar.gz | head -50
```

The output should contain entries for all three directories:

```text
volumes/etcd/
volumes/minio/
volumes/milvus/
```

Test the gzip archive:

```bash
gzip -t backups/milvus-standalone-backup.tar.gz
```

No output normally means the gzip integrity check succeeded.

## Starting Services After Backup

Restart the services:

```bash
docker compose start
```

Check their state:

```bash
docker compose ps
```

Check Milvus health:

```bash
curl http://127.0.0.1:9091/healthz
```

Run the connection example:

```bash
python examples/01_connect.py
```

## Backup Metadata

A backup should include a small text record containing:

- Backup timestamp
- Milvus version
- PyMilvus version
- etcd image version
- MinIO image version
- Docker Compose file version
- Collection names
- Backup method
- Archive checksum

Example commands:

```bash
docker compose images
python -c "import pymilvus; print(pymilvus.__version__)"
```

Version information is important because restoring with incompatible component
versions may fail.

## Creating a Checksum

Create a SHA-256 checksum:

```bash
sha256sum backups/milvus-standalone-backup.tar.gz \
  > backups/milvus-standalone-backup.tar.gz.sha256
```

Verify it later:

```bash
sha256sum -c backups/milvus-standalone-backup.tar.gz.sha256
```

Expected result:

```text
backups/milvus-standalone-backup.tar.gz: OK
```

A checksum detects archive corruption or unexpected changes.

## Copying Backups to Another Disk

A backup stored on the same disk as the active data is not sufficient protection
against disk failure.

Copy the archive and checksum to:

- Another local disk
- A secured backup server
- Object storage
- Offline storage
- A remote disaster-recovery location

The project system has a second mounted disk, so an archive can be copied there
after its path and available space are verified.

Before copying, check:

```bash
df -h
```

## Restore Overview

A cold restore follows this order:

1. Verify the backup archive and checksum.
2. Stop all Milvus-related services.
3. Preserve the current `volumes` directory.
4. Extract the backup archive.
5. Verify ownership and permissions.
6. Start etcd and MinIO.
7. Start Milvus.
8. Check logs and health.
9. Validate collections and data.

## Verifying the Backup Before Restore

Check the checksum:

```bash
sha256sum -c backups/milvus-standalone-backup.tar.gz.sha256
```

Inspect the archive:

```bash
tar -tzf backups/milvus-standalone-backup.tar.gz | head -50
```

Do not continue if the checksum fails or required directories are missing.

## Stopping Services Before Restore

Stop the stack:

```bash
docker compose stop
```

Confirm that no service is still writing:

```bash
docker compose ps
```

## Preserving Current Data

Do not immediately delete the current data.

Rename it so the operation is recoverable:

```bash
mv volumes "volumes.before-restore-$(date '+%Y-%m-%d_%H-%M-%S')"
```

This preserves the current state until the restored environment has been
validated.

Confirm that `volumes` no longer exists:

```bash
ls -ld volumes*
```

## Extracting the Backup

Extract the archive from the project root:

```bash
tar -xzf backups/milvus-standalone-backup.tar.gz
```

Because the archive contains the `volumes/` directory, extraction recreates:

```text
volumes/etcd
volumes/minio
volumes/milvus
```

Verify them:

```bash
du -sh volumes/etcd volumes/minio volumes/milvus
```

## Checking Ownership

Display ownership:

```bash
ls -ld volumes volumes/*
```

The restored files must be accessible to the corresponding container
processes.

Avoid changing ownership without first checking the ownership of a working
deployment or the user IDs expected by the container images.

## Starting the Restored Environment

Start the services:

```bash
docker compose up -d --pull never
```

Check status:

```bash
docker compose ps
```

Check Milvus health:

```bash
curl http://127.0.0.1:9091/healthz
```

## Checking Restore Logs

Inspect recent logs:

```bash
docker compose logs --tail=100 etcd
docker compose logs --tail=100 minio
docker compose logs --tail=150 standalone
```

Look for:

- Missing objects
- Metadata errors
- Permission errors
- Version incompatibility
- Failed component registration
- Storage initialization errors

## Validating the Restored Data

List collections:

```bash
python examples/01_connect.py
```

Inspect the learning collection:

```bash
python examples/02_create_collection.py
```

A more complete validation should include:

- Expected collection names
- Expected schemas
- Expected entity counts
- Expected primary keys
- Scalar query results
- Vector search results
- Index definitions
- Successful collection loading

## Functional Validation

After restore, run a query:

```python
from pymilvus import Collection, connections

connections.connect(
    alias="default",
    host="127.0.0.1",
    port="19530",
)

collection = Collection("learning_vectors")
collection.load()

rows = collection.query(
    expr="id in [1, 2, 3]",
    output_fields=["id", "label"],
)

print(rows)

collection.release()
connections.disconnect("default")
```

Then run the vector-search example:

```bash
python examples/05_search_vectors.py
```

A service being healthy does not prove that all data was restored correctly.
Functional validation is required.

## Rolling Back a Failed Restore

If validation fails:

1. Stop the restored services.
2. Rename the failed restored `volumes` directory.
3. Rename the preserved pre-restore directory back to `volumes`.
4. Start the services.
5. Validate the original environment.

Do not remove either data set until the working state is confirmed.

## etcd Snapshots

etcd supports logical snapshots through `etcdctl`.

A snapshot can provide a version-aware backup of etcd metadata.

Conceptually:

```bash
etcdctl snapshot save /backup/etcd-snapshot.db
```

A snapshot status can be inspected with:

```bash
etcdctl snapshot status /backup/etcd-snapshot.db
```

However, an etcd snapshot alone is not a complete Milvus backup. The matching
MinIO objects and Milvus local data must also be preserved consistently.

Snapshot commands, environment variables, endpoints, and restore arguments
depend on the etcd image and deployment configuration.

## MinIO Backup Considerations

Milvus stores binary data in MinIO buckets.

A MinIO backup must preserve:

- Bucket names
- Object paths
- Object content
- Required object versions, if versioning is enabled
- Access configuration needed by Milvus

Copying only selected objects without understanding Milvus segment metadata can
produce an unusable backup.

For large deployments, MinIO replication or S3-compatible backup tools may be
more appropriate than filesystem archives.

## Milvus Backup Tools

Milvus provides backup tooling for supported versions and deployment types.

A logical Milvus backup tool may:

- Discover collection metadata
- Copy related object data
- Organize collection-level backups
- Support selected restore workflows

Tool compatibility must be checked against:

- Milvus server version
- Deployment mode
- Object-storage configuration
- Authentication settings
- Backup tool version

This repository currently documents the cold filesystem backup method because
it is transparent and appropriate for the local standalone learning stack.

## Hot Backup Limitations

Copying active storage while inserts, deletes, compaction, or index building are
running can create inconsistent data.

A proper online or hot-backup solution requires mechanisms such as:

- Storage snapshots with consistency coordination
- Milvus-compatible backup tools
- Object-storage replication
- etcd snapshots
- Controlled write pauses
- Tested restore procedures

A simple filesystem copy of active directories should not be assumed to be a
valid hot backup.

## Backup Retention

A retention policy defines how long backups are kept.

Example policy:

```text
Daily backups: 7
Weekly backups: 4
Monthly backups: 6
```

A retention policy should consider:

- Available storage
- Data growth
- Recovery objectives
- Legal requirements
- Frequency of data changes
- Time required to validate backups

Do not automate deletion until backups have been successfully verified.

## Recovery Objectives

Two common backup concepts are:

### Recovery Point Objective

Recovery Point Objective, or RPO, defines how much recent data loss is
acceptable.

Example:

```text
RPO = 24 hours
```

This suggests backups should be created at least daily if losing one day of
data is acceptable.

### Recovery Time Objective

Recovery Time Objective, or RTO, defines how quickly service should be restored.

Example:

```text
RTO = 2 hours
```

Backup size, storage speed, validation time, and operational documentation all
affect RTO.

## Common Restore Failures

### Version mismatch

Restoring data created by one Milvus version into an incompatible version may
fail.

Use the same tested versions whenever possible:

```text
Milvus:   2.3.3
PyMilvus: 2.3.7
etcd:     3.5.5
```

Record the exact MinIO image identifier as well.

### Inconsistent components

Symptoms may include:

- Collections exist but cannot load
- Missing segment objects
- Search failures
- Index-loading failures
- Repeated component errors

Restore etcd, MinIO, and Milvus data from the same backup set.

### Incorrect permissions

Containers may fail to read or write restored directories.

Check:

```bash
ls -l volumes
docker compose logs
```

### Insufficient disk space

A restore may extract successfully but leave too little free space for MinIO to
operate.

Check before and after restore:

```bash
df -h
```

### Wrong extraction directory

The archive must be extracted from the project root so that it recreates the
expected `volumes/` path.

## Backup Checklist

Before backup:

- [ ] Confirm collection operations are complete
- [ ] Flush pending writes
- [ ] Check disk space
- [ ] Stop all services
- [ ] Confirm services are stopped

During backup:

- [ ] Archive `volumes/etcd`
- [ ] Archive `volumes/minio`
- [ ] Archive `volumes/milvus`
- [ ] Record component versions
- [ ] Generate a checksum

After backup:

- [ ] Test the archive
- [ ] Verify the checksum
- [ ] Copy the backup to separate storage
- [ ] Restart services
- [ ] Check Milvus health
- [ ] Record the backup result

## Restore Checklist

Before restore:

- [ ] Verify the archive checksum
- [ ] Inspect archive contents
- [ ] Confirm compatible versions
- [ ] Stop services
- [ ] Preserve the current data

During restore:

- [ ] Extract all three data directories
- [ ] Check file ownership
- [ ] Start the services
- [ ] Review logs

After restore:

- [ ] Check health
- [ ] List collections
- [ ] Verify schemas
- [ ] Verify entity counts
- [ ] Run scalar queries
- [ ] Run vector searches
- [ ] Keep the previous data until validation succeeds

## Key Lessons

- Milvus data spans multiple components.
- etcd stores critical metadata.
- MinIO stores persistent vector and index objects.
- Local Milvus storage may contain Rocksmq and runtime data.
- All components must be backed up consistently.
- Cold backup is the simplest method for this learning environment.
- A checksum verifies archive integrity.
- A backup on the same disk is not enough.
- Restore should be recoverable and fully validated.
- A successful health check alone does not prove data correctness.
