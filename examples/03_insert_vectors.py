"""Insert sample scalar and vector data into a Milvus collection."""

from pymilvus import Collection, connections, utility

MILVUS_ALIAS = "default"
MILVUS_HOST = "127.0.0.1"
MILVUS_PORT = "19530"

COLLECTION_NAME = "learning_vectors"


def main() -> None:
    """Connect to Milvus and insert sample entities into the collection."""
    connections.connect(
        alias=MILVUS_ALIAS,
        host=MILVUS_HOST,
        port=MILVUS_PORT,
    )

    try:
        if not utility.has_collection(COLLECTION_NAME):
            raise RuntimeError(
                f"Collection '{COLLECTION_NAME}' does not exist. "
                "Run examples/02_create_collection.py first."
            )

        collection = Collection(
            name=COLLECTION_NAME,
            using=MILVUS_ALIAS,
        )

        print(f"Collection: {COLLECTION_NAME}")
        print(f"Entities before insertion: {collection.num_entities}")

        if collection.num_entities > 0:
            print("The collection already contains data.")
            print("Insertion skipped to prevent duplicate primary keys.")
            return

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

        data = [
            ids,
            labels,
            embeddings,
        ]

        insert_result = collection.insert(data)

        print(f"Inserted entities: {insert_result.insert_count}")
        print(f"Primary keys: {insert_result.primary_keys}")

        collection.flush()

        print("Data flushed successfully.")
        print(f"Entities after insertion: {collection.num_entities}")

    except Exception as exc:
        print(f"Failed to insert vectors: {exc}")
        raise

    finally:
        connections.disconnect(MILVUS_ALIAS)
        print("Disconnected from Milvus.")


if __name__ == "__main__":
    main()
