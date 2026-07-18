# Vector Indexes and Similarity Metrics

This document explains how Milvus compares vectors, why vector indexes are
needed, and how to choose an appropriate index and similarity metric.

## Vector Search

Vector search finds stored vectors that are closest to a query vector.

For example, assume the collection contains:

```text
red object   -> [1.0, 0.0, 0.0, 0.0]
green object -> [0.0, 1.0, 0.0, 0.0]
blue object  -> [0.0, 0.0, 1.0, 0.0]
```

If the query vector is:

```text
[0.9, 0.1, 0.0, 0.0]
```

Milvus should return `red object` as the closest match.

To determine closeness, Milvus needs:

- A similarity or distance metric
- A vector index
- Search parameters

## What Is a Similarity Metric?

A similarity metric defines how Milvus compares two vectors.

Milvus supports several metrics. The most common metrics for floating-point
vectors are:

- L2
- Inner Product
- COSINE

The selected metric should match the embedding model and the application.

## L2 Distance

L2 is the Euclidean distance between two vectors.

For two vectors:

```text
A = [a1, a2, ..., an]
B = [b1, b2, ..., bn]
```

The distance is calculated conceptually as:

```text
sqrt((a1-b1)^2 + (a2-b2)^2 + ... + (an-bn)^2)
```

With L2:

- A smaller value means the vectors are closer.
- A distance of zero means the vectors are identical.
- Larger values indicate greater separation.

Example:

```text
A = [1.0, 0.0]
B = [0.9, 0.1]
```

These vectors have a small L2 distance and are therefore close.

L2 is useful when the absolute position and magnitude of vectors are meaningful.

## Inner Product

Inner Product, abbreviated as `IP`, compares vectors using their dot product.

Conceptually:

```text
A · B = (a1*b1) + (a2*b2) + ... + (an*bn)
```

With Inner Product:

- A larger value usually means greater similarity.
- Vector magnitude affects the result.
- Normalizing vectors is often important.

When all vectors have unit length, Inner Product and COSINE similarity produce
equivalent ranking behavior.

## COSINE Similarity

COSINE measures the angle between two vectors rather than their absolute
magnitude.

Conceptually:

```text
cosine(A, B) = (A · B) / (||A|| * ||B||)
```

With COSINE:

- A value close to `1` indicates high similarity.
- A value close to `0` indicates weak directional similarity.
- A value close to `-1` indicates opposite directions.

COSINE is commonly used for:

- Text embeddings
- Sentence embeddings
- Semantic search
- Image embeddings
- Face embeddings
- Recommendation systems

This project uses COSINE for its learning examples because its result is easy
to interpret as directional similarity.

## Metric Comparison

| Metric | Interpretation | Better result |
|---|---|---|
| `L2` | Euclidean distance | Smaller |
| `IP` | Dot-product similarity | Larger |
| `COSINE` | Angular similarity | Larger |

The index metric and search metric must match. For example, an index created
with COSINE should be searched with COSINE.

## What Is a Vector Index?

A vector index is a data structure that helps Milvus find similar vectors
efficiently.

Without an approximate index, Milvus may compare the query vector with every
stored vector. This is called exhaustive or brute-force search.

For a small collection, exhaustive search is acceptable. For millions of
vectors, it can become expensive.

An index reduces search time by organizing vectors so that Milvus examines a
smaller and more relevant part of the data.

## Exact and Approximate Search

Vector indexes can be considered in two broad categories.

### Exact search

Exact search compares against all relevant vectors and aims to return the true
nearest neighbors.

Advantages:

- Highest recall
- Simple behavior
- Useful for small datasets and testing

Disadvantages:

- Slower for large datasets
- Higher computation cost

### Approximate nearest-neighbor search

Approximate search avoids comparing every vector.

Advantages:

- Faster on large datasets
- Better scalability
- Tunable performance

Disadvantages:

- May miss some true nearest neighbors
- Requires parameter tuning
- Uses additional storage and memory

## FLAT Index

`FLAT` performs exhaustive vector comparison.

Example configuration:

```python
index_params = {
    "index_type": "FLAT",
    "metric_type": "COSINE",
    "params": {},
}
```

Advantages:

- Exact results
- No complex tuning
- Good for small collections
- Useful as a correctness baseline

Disadvantages:

- Search becomes expensive as the dataset grows
- Not appropriate for very large collections with strict latency requirements

For this project's three-vector example, FLAT is sufficient.

## IVF_FLAT Index

`IVF_FLAT` divides the vector space into clusters.

During search, Milvus examines a selected number of clusters instead of the
entire collection.

Example index configuration:

```python
index_params = {
    "index_type": "IVF_FLAT",
    "metric_type": "COSINE",
    "params": {
        "nlist": 128,
    },
}
```

The `nlist` parameter controls the number of clusters.

Search parameters include `nprobe`:

```python
search_params = {
    "metric_type": "COSINE",
    "params": {
        "nprobe": 16,
    },
}
```

- Higher `nprobe` usually improves recall.
- Higher `nprobe` also increases search time.
- `nprobe` must not be greater than `nlist`.

IVF indexes are more useful when the collection contains enough vectors to form
meaningful clusters.

## HNSW Index

HNSW stands for Hierarchical Navigable Small World.

It builds a graph in which vectors are connected to nearby vectors. During
search, Milvus navigates this graph to find close candidates efficiently.

Example configuration:

```python
index_params = {
    "index_type": "HNSW",
    "metric_type": "COSINE",
    "params": {
        "M": 16,
        "efConstruction": 200,
    },
}
```

Important HNSW parameters:

### M

`M` controls how many graph connections are created for each vector.

A larger value may:

- Improve recall
- Increase index size
- Increase memory usage
- Increase index-building time

### efConstruction

`efConstruction` controls the amount of work performed while building the
index.

A larger value may:

- Improve index quality
- Increase index-building time
- Increase resource usage during index creation

HNSW search uses the `ef` parameter:

```python
search_params = {
    "metric_type": "COSINE",
    "params": {
        "ef": 64,
    },
}
```

A larger `ef` usually improves recall but increases search latency.

## Index Comparison

| Index | Search type | Main advantage | Main limitation |
|---|---|---|---|
| `FLAT` | Exact | Maximum recall | Slow on large datasets |
| `IVF_FLAT` | Approximate | Good speed and recall balance | Requires cluster tuning |
| `HNSW` | Approximate | Fast and high-quality search | Higher memory usage |

## Recall

Recall describes how many true nearest neighbors are returned by an approximate
search.

If the exact top ten results contain ten correct neighbors and an approximate
search returns nine of them, the recall is:

```text
9 / 10 = 0.9
```

Increasing search effort usually improves recall but also increases latency.

This creates a common trade-off:

```text
Higher recall <-> Higher computation cost
```

## Choosing an Index

A simple selection guide is:

### Use FLAT when

- The collection is small.
- Exact results are required.
- You are testing correctness.
- Search performance is not yet a concern.

### Use IVF_FLAT when

- The dataset is medium or large.
- You want a configurable speed-recall balance.
- The vectors form meaningful clusters.

### Use HNSW when

- Low search latency is important.
- High recall is required.
- Additional memory usage is acceptable.
- The dataset is large enough to benefit from a graph index.

## Creating an Index with PyMilvus

An index is created on the vector field:

```python
collection.create_index(
    field_name="embedding",
    index_params={
        "index_type": "FLAT",
        "metric_type": "COSINE",
        "params": {},
    },
)
```

The scalar fields `id` and `label` are not used as the target of this vector
index.

## Inspecting Indexes

PyMilvus can display index information:

```python
for index in collection.indexes:
    print(index)
```

The collection may also expose the index parameters and indexed field name.

## Loading a Collection

Creating an index does not automatically make a collection ready for search.

The collection should be loaded:

```python
collection.load()
```

Loading prepares its segments and indexes for query execution.

When a collection is no longer needed in memory, it can be released:

```python
collection.release()
```

Releasing a collection removes it from query memory but does not delete its
stored data.

## Index Lifecycle

A simplified index lifecycle is:

```text
Create collection
       |
       v
Insert and flush vectors
       |
       v
Create vector index
       |
       v
Load collection
       |
       v
Search vectors
       |
       v
Release collection when appropriate
```

## Index and Schema Relationship

The schema defines the vector field and its dimension:

```python
FieldSchema(
    name="embedding",
    dtype=DataType.FLOAT_VECTOR,
    dim=4,
)
```

The index defines how vectors in that field are searched:

```python
{
    "index_type": "FLAT",
    "metric_type": "COSINE",
    "params": {},
}
```

The schema and index have different responsibilities:

- Schema defines what data may be stored.
- Index defines how vector search is accelerated.

## Common Errors

### Metric mismatch

An index created with COSINE should not be searched with L2.

Keep the metric consistent:

```text
Index metric:  COSINE
Search metric: COSINE
```

### Incorrect vector dimension

If the collection dimension is four, the query vector must also contain four
values.

Valid:

```python
[0.9, 0.1, 0.0, 0.0]
```

Invalid:

```python
[0.9, 0.1, 0.0]
```

### Collection not loaded

Search may fail if the collection has not been loaded:

```python
collection.load()
```

### Invalid index parameters

Index parameters must match the selected index type. For example, HNSW uses
`M` and `efConstruction`, while IVF_FLAT uses `nlist`.

## Example Configuration for This Project

The learning collection is very small, so the example uses:

```text
Index type: FLAT
Metric:     COSINE
Field:      embedding
Dimension:  4
```

This configuration prioritizes simplicity and exact results.

Later, the same collection structure can be tested with HNSW to demonstrate
approximate nearest-neighbor search.

## Practical Face-Recognition Example

A face-recognition collection might use:

```text
Vector dimension: 512
Metric: COSINE
Index type: HNSW
```

Example HNSW parameters:

```python
{
    "index_type": "HNSW",
    "metric_type": "COSINE",
    "params": {
        "M": 16,
        "efConstruction": 200,
    },
}
```

The correct parameters depend on:

- Number of vectors
- Available memory
- Required latency
- Required recall
- Frequency of index creation
- Hardware resources

Parameters should be measured with representative data rather than selected
only from general recommendations.

## Next Step

The next document, `05-insert-and-search.md`, explains how entities are
inserted, flushed, loaded, queried, and searched using PyMilvus.
