"""Create an HNSW index for the vector field in Milvus."""

from pymilvus import Collection, connections, utility

MILVUS_ALIAS = "default"
MILVUS_HOST = "127.0.0.1"
MILVUS_PORT = "19530"

COLLECTION_NAME = "learning_vectors"
VECTOR_FIELD = "embedding"


def main() -> None:
    """Connect to Milvus and create an HNSW index."""
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

        collection = Collection(COLLECTION_NAME)

        if collection.indexes:
            print(f"An index already exists on collection: {COLLECTION_NAME}")

            for index in collection.indexes:
                print(f"Field: {index.field_name}")
                print(f"Index parameters: {index.params}")

            return

        index_params = {
            "index_type": "HNSW",
            "metric_type": "COSINE",
            "params": {
                "M": 16,
                "efConstruction": 200,
            },
        }

        print(f"Creating index on field: {VECTOR_FIELD}")

        collection.create_index(
            field_name=VECTOR_FIELD,
            index_params=index_params,
        )

        print("Index created successfully.")
        print(f"Collection: {COLLECTION_NAME}")
        print(f"Vector field: {VECTOR_FIELD}")
        print("Index type: HNSW")
        print("Metric type: COSINE")
        print("M: 16")
        print("efConstruction: 200")

    except Exception as exc:
        print(f"Index creation failed: {exc}")
        raise

    finally:
        connections.disconnect(MILVUS_ALIAS)
        print("Disconnected from Milvus.")


if __name__ == "__main__":
    main()
