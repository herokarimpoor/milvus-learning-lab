# Milvus Learning Lab

A practical, hands-on learning repository for understanding Milvus, vector
databases, similarity search, indexing, and data management with Python.

This repository combines structured documentation, executable examples,
troubleshooting notes, and a face-recognition use case.

## Project Goals

- Understand vector databases and their use cases
- Run Milvus locally with Docker Compose
- Connect to Milvus using PyMilvus
- Create collections and define schemas
- Insert, query, search, and delete vector data
- Compare similarity metrics and index types
- Understand the roles of Milvus, etcd, and MinIO
- Learn backup and restore principles
- Diagnose common operational problems
- Build a simplified face-recognition example using 512-dimensional vectors

## Technology Stack

- Milvus 2.3.3
- PyMilvus 2.3.7
- Python 3.10
- Docker
- Docker Compose
- etcd
- MinIO

## Repository Structure

```text
milvus-learning-lab/
├── docs/                       # Conceptual and operational documentation
├── examples/                   # Executable PyMilvus examples
├── face-recognition-demo/      # Face-vector search example
├── troubleshooting/            # Common errors and diagnostic guides
├── docker-compose.yml          # Local Milvus environment
├── requirements.txt            # Python dependencies
└── README.md                   # Project overview
```


## Learning Path

1. [Introduction to Milvus](docs/01-introduction.md)
2. [Milvus Architecture](docs/02-architecture.md)
3. [Collections and Schemas](docs/03-collections-and-schema.md)
4. [Indexes and Distance Metrics](docs/04-indexes-and-metrics.md)
5. [Insert and Search Operations](docs/05-insert-and-search.md)
6. [Backup and Restore](docs/06-backup-and-restore.md)

## Python Environment

This project uses Python 3.10.

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Verify the installation:

```bash
python -c "import pymilvus; print(pymilvus.__version__)"
```

## Running Milvus

The local environment includes:

- Milvus for vector storage and similarity search
- etcd for metadata and coordination
- MinIO for persistent object storage

The services are managed through Docker Compose.

## Examples

The `examples` directory covers:

- Connecting to Milvus
- Creating a collection
- Inserting vectors
- Creating an index
- Searching for similar vectors
- Querying and deleting entities

## Practical Use Case

The `face-recognition-demo` directory demonstrates how a face embedding can be
stored and searched in Milvus.

The example uses:

- 512-dimensional vectors
- COSINE similarity
- HNSW indexing
- Metadata associated with each face vector

## Troubleshooting

Operational notes are available for:

- Connection failures
- Collection loading problems
- Milvus, MinIO, and etcd inconsistencies
- Index and vector-dimension errors
- Backup and restore issues

## License

This project is licensed under the MIT License.

## Author

Created by [herokarimpoor](https://github.com/herokarimpoor) as a practical
Milvus learning and portfolio project.
