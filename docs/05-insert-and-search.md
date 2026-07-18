# Insert, Query, and Vector Search

This document explains how data is inserted into Milvus and how scalar queries
and vector similarity searches are performed using PyMilvus.

The examples use the collection:

```text
learning_vectors
```

Its schema contains:

| Field | Type | Purpose |
|---|---|---|
| `id` | `INT64` | Primary key |
| `label` | `VARCHAR` | Text metadata |
| `embedding` | `FLOAT_VECTOR` | Four-dimensional vector |

## Operation Sequence

The learning workflow follows this order:

```text
Connect to Milvus
       |
       v
Create the collection
       |
       v
Insert entities
       |
       v
Flush pending data
       |
       v
Create a vector index
       |
       v
Load the collection
       |
       v
Query or search
       |
       v
Release and disconnect
```

Each step has a different responsibility.

## Opening an Existing Collection

Before inserting or searching, the program opens the collection:

```python
collection = Collection(
    name="learning_vectors",
    using="default",
)
```

This does not create a new collection. It creates a Python object connected to
the existing collection in Milvus.

The collection should be created first by running:

```bash
python examples/02_create_collection.py
```

## Sample Data

The insert example uses three entities:

| ID | Label | Embedding |
|---:|---|---|
| `1` | `red object` | `[1.0, 0.0, 0.0, 0.0]` |
| `2` | `green object` | `[0.0, 1.0, 0.0, 0.0]` |
| `3` | `blue object` | `[0.0, 0.0, 1.0, 0.0]` |

These vectors are intentionally simple. Each vector points mostly in a
different direction, making similarity results easy to understand.

## Column-Based Insert Format

The example prepares one list for each schema field:

```python
ids = [1, 2, 3]

labels = [
    "red object",
    "green object",
    "blue object",
]

embeddings = [
    [1.0, 0.0, 0.0, 0.0],
    [0.0, 1.0, 0.0, 0.0],
    [0.0, 0.0, 1.0, 0.0],
]
```

The lists are provided in the same order as the collection fields:

```python
data = [
    ids,
    labels,
    embeddings,
]
```

The number of values in every field must match.

In this example:

```text
3 IDs
3 labels
3 vectors
```

If the lists contain different numbers of items, the insert operation fails.

## Inserting Entities

Data is inserted with:

```python
insert_result = collection.insert(data)
```

The result contains useful information:

```python
print(insert_result.insert_count)
print(insert_result.primary_keys)
```

Expected values:

```text
Inserted entities: 3
Primary keys: [1, 2, 3]
```

The insert response means Milvus accepted the request. The application may
still need to wait for persistence or select an appropriate consistency
strategy before immediately reading the new data.

## Primary-Key Responsibility

The collection uses:

```python
auto_id=False
```

Therefore, the application supplies every primary-key value.

Milvus should not be treated like a relational database that always performs an
immediate uniqueness check before every insert. Applications should avoid
inserting the same primary key repeatedly.

The learning example checks the collection entity count and skips insertion
when data already exists:

```python
if collection.num_entities > 0:
    print("Insertion skipped to prevent duplicate primary keys.")
    return
```

This is suitable for the controlled tutorial collection. A real application
should use a more precise idempotency strategy, such as:

- Tracking inserted identifiers in an application database
- Querying expected identifiers when appropriate
- Using deterministic primary keys
- Using an upsert operation when supported and intended
- Designing retry logic carefully

## Flushing Data

The example calls:

```python
collection.flush()
```

A flush asks Milvus to persist pending insert data.

During persistence, Milvus coordinates:

- Segment state
- Metadata in etcd
- Insert logs in MinIO
- Scalar-field data
- Vector-field data
- Statistics information

After a successful flush, the example prints:

```text
Data flushed successfully.
```

## Why Flush Can Fail

A flush depends on the health of the Milvus storage components.

It may fail when:

- MinIO is unavailable
- etcd is unavailable
- Disk space is too low
- Milvus stops during the operation
- Network communication between containers fails
- Storage permissions are incorrect

A disk-space failure may produce:

```text
Storage backend has reached its minimum free drive threshold
```

The available disk space can be checked with:

```bash
df -h
```

## Counting Entities

The collection exposes:

```python
collection.num_entities
```

Example:

```text
Entities after insertion: 3
```

The entity count is useful for basic inspection, but it should not replace
precise validation in production applications.

Repeated insert attempts, delayed persistence, and duplicate identifiers can
make a simple physical count different from the number of unique logical
records expected by an application.

## Creating the Vector Index

Before searching, an index is created on the vector field.

The learning example uses a FLAT index with COSINE similarity:

```python
index_params = {
    "index_type": "FLAT",
    "metric_type": "COSINE",
    "params": {},
}

collection.create_index(
    field_name="embedding",
    index_params=index_params,
)
```

FLAT is appropriate for this small collection because it performs exact vector
comparison and does not require tuning.

## Loading the Collection

The collection must be loaded before query and vector search operations:

```python
collection.load()
```

Loading makes collection data available to Milvus query processing.

For a large collection, loading may require significant memory and time.

## Waiting for Load Completion

The `load()` operation may return after initiating the load process, depending
on the client and server behavior.

Milvus utilities can be used to wait until loading completes:

```python
utility.wait_for_loading_complete("learning_vectors")
```

For a small local collection, loading normally completes quickly.

## Scalar Query

A scalar query retrieves entities using a Boolean expression rather than vector
similarity.

Example:

```python
results = collection.query(
    expr="id in [1, 2, 3]",
    output_fields=["id", "label", "embedding"],
)
```

Expected result conceptually:

```text
[
    {
        "id": 1,
        "label": "red object",
        "embedding": [1.0, 0.0, 0.0, 0.0]
    },
    {
        "id": 2,
        "label": "green object",
        "embedding": [0.0, 1.0, 0.0, 0.0]
    },
    {
        "id": 3,
        "label": "blue object",
        "embedding": [0.0, 0.0, 1.0, 0.0]
    }
]
```

## Query Expressions

Milvus supports expressions for filtering scalar fields.

Examples:

```python
expr="id == 1"
```

```python
expr="id in [1, 3]"
```

```python
expr="id >= 2"
```

```python
expr='label == "red object"'
```

The supported expression behavior depends on the Milvus version and field
types.

## Vector Search

A vector search uses one or more query vectors:

```python
query_vectors = [
    [0.9, 0.1, 0.0, 0.0],
]
```

This vector points mostly in the same direction as:

```text
[1.0, 0.0, 0.0, 0.0]
```

Therefore, `red object` should be the closest result.

## Search Parameters

For a FLAT index using COSINE:

```python
search_params = {
    "metric_type": "COSINE",
    "params": {},
}
```

The metric must match the metric used when creating the index.

## Running the Search

The search operation is:

```python
results = collection.search(
    data=query_vectors,
    anns_field="embedding",
    param=search_params,
    limit=3,
    output_fields=["label"],
)
```

Parameters:

- `data` contains the query vectors.
- `anns_field` identifies the vector field.
- `param` contains metric and search parameters.
- `limit` specifies the maximum number of matches.
- `output_fields` specifies scalar metadata returned with each match.

## Search Results

Milvus returns one result group for each query vector.

The results can be inspected as follows:

```python
for query_number, hits in enumerate(results, start=1):
    print(f"Query {query_number}:")

    for hit in hits:
        print(
            f"id={hit.id}, "
            f"label={hit.entity.get('label')}, "
            f"score={hit.distance}"
        )
```

With COSINE similarity, the expected ranking is approximately:

```text
1. red object
2. green object
3. blue object
```

The exact scores depend on the query vector and metric implementation.

## Distance Versus Similarity

PyMilvus may expose the result value through:

```python
hit.distance
```

The interpretation depends on the metric:

| Metric | Better match |
|---|---|
| `L2` | Smaller value |
| `IP` | Larger value |
| `COSINE` | Larger value |

Therefore, the field name `distance` does not always mean that a smaller value
is better.

## Filtering During Search

A scalar expression can be combined with vector search.

Example:

```python
results = collection.search(
    data=query_vectors,
    anns_field="embedding",
    param=search_params,
    limit=3,
    expr="id >= 2",
    output_fields=["label"],
)
```

This search ignores the entity with `id=1`, even if it is the closest vector.

Hybrid filtering is useful when vector similarity must be combined with
business conditions such as:

- User access rules
- Document category
- Date range
- Product availability
- Tenant identifier
- Person status

## Multiple Query Vectors

Milvus can search multiple vectors in one request:

```python
query_vectors = [
    [0.9, 0.1, 0.0, 0.0],
    [0.0, 0.8, 0.2, 0.0],
]
```

The result contains two groups:

```text
results[0] -> matches for the first query vector
results[1] -> matches for the second query vector
```

Batch search reduces the number of separate client requests.

## Search Limit

The `limit` parameter controls the number of nearest matches:

```python
limit=3
```

This is commonly called `top-k`.

Examples:

```text
limit=1  -> return the closest match
limit=5  -> return the five closest matches
limit=10 -> return the ten closest matches
```

Choosing a larger limit returns more candidates but may increase processing and
response size.

## Releasing the Collection

After the operations are complete, the collection can be released:

```python
collection.release()
```

Release means:

- Remove the collection from query memory.
- Preserve the collection schema.
- Preserve stored entities.
- Preserve index files.

Release is not the same as deletion.

## Disconnecting the Client

The PyMilvus connection should be closed:

```python
connections.disconnect("default")
```

A `finally` block ensures disconnection even when an error occurs:

```python
finally:
    connections.disconnect("default")
```

## Error Handling

The examples use:

```python
except Exception as exc:
    print(f"Operation failed: {exc}")
    raise
```

Printing the error helps with local troubleshooting. Raising it again ensures
the script exits with a failure status instead of silently continuing.

## Common Insert Errors

### Collection does not exist

Run:

```bash
python examples/02_create_collection.py
```

### Incorrect vector dimension

The collection expects four values per vector.

Valid:

```python
[1.0, 0.0, 0.0, 0.0]
```

Invalid:

```python
[1.0, 0.0, 0.0]
```

### Field lengths do not match

Invalid example:

```text
3 IDs
2 labels
3 vectors
```

Each field must contain the same number of entities.

### Disk space is too low

Check:

```bash
df -h
```

MinIO requires sufficient free disk space to persist Milvus objects.

## Common Search Errors

### Index does not exist

Create an index before loading and searching:

```bash
python examples/04_create_index.py
```

### Collection is not loaded

Load it:

```python
collection.load()
```

### Metric mismatch

Use the same metric for index creation and search:

```text
Index:  COSINE
Search: COSINE
```

### Incorrect query-vector dimension

A four-dimensional collection requires four-dimensional query vectors.

### Output field does not exist

Only request scalar fields defined in the collection schema.

## Running the Learning Workflow

Start the services:

```bash
docker compose up -d --pull never
```

Check health:

```bash
curl http://127.0.0.1:9091/healthz
```

Create the collection:

```bash
python examples/02_create_collection.py
```

Insert sample vectors:

```bash
python examples/03_insert_vectors.py
```

Create the index:

```bash
python examples/04_create_index.py
```

Search the vectors:

```bash
python examples/05_search_vectors.py
```

## Data Persistence Test

A simple persistence test is:

1. Insert and flush the entities.
2. Stop the containers.
3. Start the containers again.
4. Reconnect to Milvus.
5. Check the entity count.
6. Query the expected identifiers.

Commands:

```bash
docker compose stop
docker compose start
python examples/02_create_collection.py
```

If all persistent directories remain intact, the collection metadata and
successfully flushed entities should remain available.

## Practical Application Flow

A real embedding application commonly follows this pattern:

```text
Raw input
   |
   v
Embedding model
   |
   v
Fixed-dimensional vector
   |
   v
Insert vector and metadata into Milvus
   |
   v
Create or maintain an index
   |
   v
Convert a new input into a query vector
   |
   v
Search Milvus
   |
   v
Apply application thresholds and business rules
```

Milvus stores and searches vectors, but it does not normally generate the
embeddings. An external machine-learning model produces the vectors.

## Key Lessons

- Insert data in schema-field order.
- All inserted fields must have equal row counts.
- Every vector must match the configured dimension.
- Avoid uncontrolled repeated insertion of primary keys.
- Flush operations require healthy persistent storage.
- Create a vector index before search.
- Load the collection before query and search.
- Keep index and search metrics consistent.
- Interpret scores according to the selected metric.
- Always monitor disk space and service health.

## Next Step

The next document, `06-backup-and-restore.md`, explains why a complete Milvus
backup must preserve the related Milvus, etcd, and MinIO data consistently.
