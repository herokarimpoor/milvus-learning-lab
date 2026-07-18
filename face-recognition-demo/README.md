
# Face Embedding Search Demo

This example demonstrates how Milvus can store and search
512-dimensional face embeddings.

The demo uses generated vectors instead of real face images. Its purpose is to
explain the vector-database part of a face-recognition system without requiring
a face-detection or embedding model.

## Learning Goals

This example demonstrates how to:

- Create a collection for face embeddings
- Store a unique identifier and a person's name
- Store 512-dimensional vectors
- Normalize vectors before insertion and search
- Create an HNSW index
- Use COSINE similarity
- Search for the most similar face embedding
- Retrieve metadata with search results

## Collection Schema

The `face_embeddings_demo` collection contains the following fields:

| Field | Data type | Description |
|---|---|---|
| `face_id` | `INT64` | Primary key for the face record |
| `person_name` | `VARCHAR` | Name associated with the embedding |
| `embedding` | `FLOAT_VECTOR` | 512-dimensional face embedding |

## Index Configuration

The vector field uses the following index configuration:

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

The search configuration uses:

```python
{
    "metric_type": "COSINE",
    "params": {
        "ef": 64,
    },
}
```

## How the Demo Works

The program performs these steps:

1. Connects to Milvus.
2. Creates the collection if it does not already exist.
3. Generates three deterministic 512-dimensional vectors.
4. Normalizes the vectors to unit length.
5. Stores sample records for Alice, Bob, and Carol.
6. Creates an HNSW index.
7. Generates a query vector similar to Alice's embedding.
8. Searches for the three closest vectors.
9. Displays the face ID, person name, and similarity score.

## Run the Demo

Start Milvus from the repository root:

```bash
docker compose up -d --pull never
```

Activate the Python environment:

```bash
source .venv/bin/activate
```

Run the example:

```bash
python face-recognition-demo/face_search_demo.py
```

Example output:

```text
Connected to Milvus.
Collection created: face_embeddings_demo
Inserted faces: 3
HNSW index created successfully.

Face-search results:
1. face_id=101, person_name=Alice, similarity=0.975908
2. face_id=103, person_name=Carol, similarity=-0.009694
3. face_id=102, person_name=Bob, similarity=-0.042546

Best match: Alice (similarity=0.975908)
Collection released from memory.
Disconnected from Milvus.
```

## Understanding the Similarity Score

COSINE similarity measures the direction of two vectors.

Its theoretical range is from `-1` to `1`:

* A value close to `1` indicates high similarity.
* A value close to `0` indicates little directional similarity.
* A negative value indicates that the vectors point in different directions.

A production face-recognition system must define and validate a matching
threshold using real evaluation data. The threshold should not be selected
only from this synthetic demonstration.

## Synthetic Versus Real Face Embeddings

This demo does not read face images and does not perform face detection.

In a real application, a face-recognition model performs these steps:

1. Detect a face in an image.
2. Align and preprocess the detected face.
3. Generate a face embedding.
4. Normalize the embedding.
5. Store or search the embedding in Milvus.
6. Apply a validated similarity threshold.
7. Return a match or classify the face as unknown.

Models such as InsightFace can generate real 512-dimensional face embeddings.
Milvus stores and searches those embeddings, but it does not detect faces or
generate embeddings itself.

## Limitations

This example is intended for learning purposes.

It does not include:

* Face detection
* Face alignment
* Image-quality validation
* Liveness or anti-spoofing detection
* Real identity verification
* Threshold calibration
* Duplicate-person management
* Privacy and security controls

These components must be designed separately for a production system
