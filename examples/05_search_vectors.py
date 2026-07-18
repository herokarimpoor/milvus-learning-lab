"""Search for similar vectors in a Milvus collection."""

from pymilvus import Collection, connections, utility

MILVUS_ALIAS = "default"
MILVUS_HOST = "127.0.0.1"
MILVUS_PORT = "19530"

COLLECTION_NAME = "learning_vectors"
VECTOR_FIELD = "embedding"


def main() -> None:
    """Load the collection and perform a vector similarity search."""
    collection = None

    try:
        connections.connect(
            alias=MILVUS_ALIAS,
            host=MILVUS_HOST,
            port=MILVUS_PORT,
        )

        if not utility.has_collection(COLLECTION_NAME):
            raise RuntimeError(
                f"Collection '{COLLECTION_NAME}' does not exist. "
                "Run examples/02_create_collection.py first."
            )

        collection = Collection(
            name=COLLECTION_NAME,
            using=MILVUS_ALIAS,
        )

        if collection.num_entities == 0:
            raise RuntimeError(
                "The collection contains no data. "
                "Run examples/03_insert_vectors.py first."
            )

        if not collection.indexes:
            raise RuntimeError(
                "The collection has no index. "
                "Run examples/04_create_index.py first."
            )

        print(f"Loading collection: {COLLECTION_NAME}")
        collection.load()

        query_vectors = [
            [0.9, 0.1, 0.0, 0.0],
        ]

        search_params = {
            "metric_type": "COSINE",
            "params": {
                "ef": 64,
            },
        }

        print(f"Query vector: {query_vectors[0]}")
        print("Searching for the 3 most similar vectors...")

        results = collection.search(
            data=query_vectors,
            anns_field=VECTOR_FIELD,
            param=search_params,
            limit=3,
            output_fields=["label"],
        )

        for query_number, hits in enumerate(results, start=1):
            print(f"\nResults for query {query_number}:")

            for rank, hit in enumerate(hits, start=1):
                label = hit.entity.get("label")

                print(
                    f"{rank}. "
                    f"id={hit.id}, "
                    f"label={label}, "
                    f"similarity={hit.distance:.6f}"
                )

    except Exception as exc:
        print(f"Vector search failed: {exc}")
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
