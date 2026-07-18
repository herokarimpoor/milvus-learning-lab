"""Create a Milvus collection with scalar and vector fields."""

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

COLLECTION_NAME = "learning_vectors"
VECTOR_DIMENSION = 4


def main() -> None:
    """Connect to Milvus and create a collection if it does not exist."""
    connections.connect(
        alias=MILVUS_ALIAS,
        host=MILVUS_HOST,
        port=MILVUS_PORT,
    )

    try:
        if utility.has_collection(COLLECTION_NAME):
            collection = Collection(
                name=COLLECTION_NAME,
                using=MILVUS_ALIAS,
            )
            print(f"Collection already exists: {COLLECTION_NAME}")
        else:
            fields = [
                FieldSchema(
                    name="id",
                    dtype=DataType.INT64,
                    is_primary=True,
                    auto_id=False,
                ),
                FieldSchema(
                    name="label",
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
                description="A collection for learning Milvus operations",
                enable_dynamic_field=False,
            )

            collection = Collection(
                name=COLLECTION_NAME,
                schema=schema,
                using=MILVUS_ALIAS,
            )

            print(f"Collection created successfully: {COLLECTION_NAME}")

        print(f"Collection description: {collection.description}")
        print(f"Number of entities: {collection.num_entities}")
        print("Schema fields:")

        for field in collection.schema.fields:
            print(f"- {field.name}: {field.dtype}")

    except Exception as exc:
        print(f"Failed to create or inspect the collection: {exc}")
        raise

    finally:
        connections.disconnect(MILVUS_ALIAS)
        print("Disconnected from Milvus.")


if __name__ == "__main__":
    main()
