"""Demonstrate face-embedding storage and similarity search with Milvus."""

import numpy as np
from pymilvus import (
    Collection,
    CollectionSchema,
    DataType,
    FieldSchema,
    connections,
    utility,
)

MILVUS_ALIAS = "default"
MILVUS_HOST = "127.0.0.1"
MILVUS_PORT = "19530"

COLLECTION_NAME = "face_embeddings_demo"
VECTOR_DIMENSION = 512


def normalize(vector: np.ndarray) -> np.ndarray:
    """Return a vector normalized to unit length."""
    norm = np.linalg.norm(vector)

    if norm == 0:
        raise ValueError("A zero vector cannot be normalized.")

    return vector / norm


def create_collection() -> Collection:
    """Create or open the face-embedding collection."""
    if utility.has_collection(COLLECTION_NAME):
        print(f"Collection already exists: {COLLECTION_NAME}")
        return Collection(COLLECTION_NAME, using=MILVUS_ALIAS)

    fields = [
        FieldSchema(
            name="face_id",
            dtype=DataType.INT64,
            is_primary=True,
            auto_id=False,
        ),
        FieldSchema(
            name="person_name",
            dtype=DataType.VARCHAR,
            max_length=100,
        ),
        FieldSchema(
            name="embedding",
            dtype=DataType.FLOAT_VECTOR,
            dim=VECTOR_DIMENSION,
        ),
    ]

    schema = CollectionSchema(
        fields=fields,
        description="Demo collection for 512-dimensional face embeddings",
    )

    collection = Collection(
        name=COLLECTION_NAME,
        schema=schema,
        using=MILVUS_ALIAS,
    )

    print(f"Collection created: {COLLECTION_NAME}")
    return collection


def generate_embeddings() -> np.ndarray:
    """Generate deterministic sample face embeddings."""
    random_generator = np.random.default_rng(seed=42)
    embeddings = random_generator.normal(
        size=(3, VECTOR_DIMENSION)
    ).astype(np.float32)

    return np.array(
        [normalize(embedding) for embedding in embeddings],
        dtype=np.float32,
    )


def insert_sample_faces(
    collection: Collection,
    embeddings: np.ndarray,
) -> None:
    """Insert sample face records when the collection is empty."""
    if collection.num_entities > 0:
        print(
            f"Insertion skipped: collection already contains "
            f"{collection.num_entities} entities."
        )
        return

    face_ids = [101, 102, 103]
    person_names = ["Alice", "Bob", "Carol"]

    result = collection.insert(
        [
            face_ids,
            person_names,
            embeddings.tolist(),
        ]
    )

    collection.flush()

    print(f"Inserted faces: {result.insert_count}")
    print(f"Primary keys: {result.primary_keys}")


def create_index(collection: Collection) -> None:
    """Create an HNSW index when no vector index exists."""
    if collection.indexes:
        print("Vector index already exists.")
        return

    collection.create_index(
        field_name="embedding",
        index_params={
            "index_type": "HNSW",
            "metric_type": "COSINE",
            "params": {
                "M": 16,
                "efConstruction": 200,
            },
        },
    )

    print("HNSW index created successfully.")


def search_similar_face(
    collection: Collection,
    embeddings: np.ndarray,
) -> None:
    """Create a query similar to Alice and search for matching faces."""
    noise_generator = np.random.default_rng(seed=100)
    noise = noise_generator.normal(
        scale=0.01,
        size=VECTOR_DIMENSION,
    ).astype(np.float32)

    query_embedding = normalize(embeddings[0] + noise)

    collection.load()

    results = collection.search(
        data=[query_embedding.tolist()],
        anns_field="embedding",
        param={
            "metric_type": "COSINE",
            "params": {
                "ef": 64,
            },
        },
        limit=3,
        output_fields=["person_name"],
    )

    print("\nFace-search results:")

    for rank, hit in enumerate(results[0], start=1):
        person_name = hit.entity.get("person_name")

        print(
            f"{rank}. "
            f"face_id={hit.id}, "
            f"person_name={person_name}, "
            f"similarity={hit.distance:.6f}"
        )

    best_match = results[0][0]

    print(
        f"\nBest match: {best_match.entity.get('person_name')} "
        f"(similarity={best_match.distance:.6f})"
    )


def main() -> None:
    """Run the complete face-embedding demonstration."""
    collection = None

    try:
        connections.connect(
            alias=MILVUS_ALIAS,
            host=MILVUS_HOST,
            port=MILVUS_PORT,
        )

        print("Connected to Milvus.")

        embeddings = generate_embeddings()
        collection = create_collection()

        insert_sample_faces(collection, embeddings)
        create_index(collection)
        search_similar_face(collection, embeddings)

    except Exception as exc:
        print(f"Face-search demo failed: {exc}")
        raise

    finally:
        if collection is not None:
            try:
                collection.release()
                print("Collection released from memory.")
            except Exception:
                pass

        connections.disconnect(MILVUS_ALIAS)
        print("Disconnected from Milvus.")


if __name__ == "__main__":
    main()
