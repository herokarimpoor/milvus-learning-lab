"""Query scalar data and delete an entity from a Milvus collection."""

from pymilvus import Collection, connections, utility

MILVUS_ALIAS = "default"
MILVUS_HOST = "127.0.0.1"
MILVUS_PORT = "19530"

COLLECTION_NAME = "learning_vectors"
DELETE_ID = 3


def print_entities(title: str, entities: list) -> None:
    """Print queried entities in primary-key order."""
    print(f"\n{title}")

    if not entities:
        print("No entities found.")
        return

    for entity in sorted(entities, key=lambda item: item["id"]):
        print(f"- id={entity['id']}, label={entity['label']}")


def main() -> None:
    """Query entities, delete one entity, and verify the deletion."""
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

        print(f"Loading collection: {COLLECTION_NAME}")
        collection.load()

        entities_before = collection.query(
            expr="id in [1, 2, 3]",
            output_fields=["id", "label"],
        )

        print_entities("Entities before deletion:", entities_before)

        target = collection.query(
            expr=f"id == {DELETE_ID}",
            output_fields=["id", "label"],
        )

        if not target:
            print(f"\nEntity with id={DELETE_ID} has already been deleted.")
            return

        print(f"\nDeleting entity with id={DELETE_ID}...")
        delete_result = collection.delete(expr=f"id == {DELETE_ID}")
        collection.flush()

        print(f"Deleted entities: {delete_result.delete_count}")

        entities_after = collection.query(
            expr="id in [1, 2, 3]",
            output_fields=["id", "label"],
        )

        print_entities("Entities after deletion:", entities_after)

        deleted_entity = collection.query(
            expr=f"id == {DELETE_ID}",
            output_fields=["id", "label"],
        )

        if deleted_entity:
            raise RuntimeError(
                f"Deletion verification failed for id={DELETE_ID}."
            )

        print(f"\nDeletion verified: id={DELETE_ID} no longer exists.")

    except Exception as exc:
        print(f"Query or deletion failed: {exc}")
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
