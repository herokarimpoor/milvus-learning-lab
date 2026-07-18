"""Connect to Milvus and display basic server information."""

from pymilvus import connections, utility

MILVUS_ALIAS = "default"
MILVUS_HOST = "127.0.0.1"
MILVUS_PORT = "19530"


def main() -> None:
    """Connect to Milvus, inspect the server, and close the connection."""
    try:
        connections.connect(
            alias=MILVUS_ALIAS,
            host=MILVUS_HOST,
            port=MILVUS_PORT,
        )

        print("Connected to Milvus successfully.")
        print(f"Server version: {utility.get_server_version()}")
        print(f"Collections: {utility.list_collections()}")

    except Exception as exc:
        print(f"Milvus connection failed: {exc}")
        raise

    finally:
        connections.disconnect(MILVUS_ALIAS)
        print("Disconnected from Milvus.")


if __name__ == "__main__":
    main()
