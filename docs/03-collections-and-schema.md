# Collections and Schemas in Milvus

This document explains how collections and schemas work in Milvus and describes
the implementation in `examples/02_create_collection.py`.

## What Is a Collection?

A collection is the main data container in Milvus. It is similar to a table in
a relational database.

A collection contains:

- A unique name
- A schema
- Scalar fields
- One or more vector fields
- Entities containing the stored data
- Optional indexes for efficient vector search

The example creates a collection named:

```text
learning_vectors
```

## What Is an Entity?

An entity is one record stored in a collection. It is comparable to a row in a
relational database.

An entity in this project contains:

- A unique integer identifier
- A text label
- A four-dimensional floating-point vector

An example entity could look like this:

```text
id: 1
label: "document-one"
embedding: [0.1, 0.2, 0.3, 0.4]
```

## What Is a Schema?

A schema defines the structure of the entities stored in a collection.

It determines:

- The names of the fields
- The data type of each field
- The primary-key field
- The vector dimension
- Field-specific constraints
- Whether dynamic fields are allowed

The schema for the `learning_vectors` collection contains three fields:

| Field | Data type | Purpose |
|---|---|---|
| `id` | `INT64` | Unique primary key |
| `label` | `VARCHAR` | Text metadata |
| `embedding` | `FLOAT_VECTOR` | Four-dimensional vector |

## Collection Configuration

The example defines the collection name and vector dimension as constants:

```python
COLLECTION_NAME = "learning_vectors"
VECTOR_DIMENSION = 4
```

Every vector inserted into this collection must contain exactly four
floating-point values.

For example:

```python
[0.1, 0.2, 0.3, 0.4]
```

The small dimension is used to keep the learning examples simple. Real
embedding models commonly generate much larger vectors, such as 128, 384, 512,
768, or 1536 dimensions.

## Connecting to Milvus

Before creating or opening the collection, the program connects to the local
Milvus server:

```python
connections.connect(
    alias=MILVUS_ALIAS,
    host=MILVUS_HOST,
    port=MILVUS_PORT,
)
```

The example uses:

```text
Host: 127.0.0.1
Port: 19530
Alias: default
```

Port `19530` is the default client communication port used by Milvus.

## Checking Whether the Collection Exists

The program first checks whether the collection already exists:

```python
if utility.has_collection(COLLECTION_NAME):
```

If the collection exists, it is opened without changing its schema:

```python
collection = Collection(
    name=COLLECTION_NAME,
    using=MILVUS_ALIAS,
)
```

This makes the example safe to run multiple times. It does not attempt to create
a duplicate collection.

## Defining the Primary Key

The first field is the primary key:

```python
FieldSchema(
    name="id",
    dtype=DataType.INT64,
    is_primary=True,
    auto_id=False,
)
```

The field has the following properties:

- Its name is `id`.
- Its data type is `INT64`.
- It uniquely identifies every entity.
- Its value must be supplied by the application because `auto_id` is disabled.

Primary-key values must be unique. Inserting duplicate identifiers can cause an
entity to be replaced or produce results that are difficult to interpret,
depending on the Milvus operation and consistency behavior.

## Defining the Text Field

The second field stores text metadata:

```python
FieldSchema(
    name="label",
    dtype=DataType.VARCHAR,
    max_length=100,
)
```

The `label` field can store strings with a maximum length of 100 characters.

Scalar metadata can be returned with search results and used in filtering
expressions.

## Defining the Vector Field

The third field stores vectors:

```python
FieldSchema(
    name="embedding",
    dtype=DataType.FLOAT_VECTOR,
    dim=VECTOR_DIMENSION,
)
```

The vector field has the following properties:

- Its name is `embedding`.
- It stores floating-point vectors.
- Every vector must have exactly four dimensions.
- It will later be used for similarity search.

Milvus compares vectors using a selected distance or similarity metric, such as
L2, Inner Product, or COSINE.

## Creating the Collection Schema

The fields are combined into a collection schema:

```python
schema = CollectionSchema(
    fields=fields,
    description="A collection for learning Milvus operations",
    enable_dynamic_field=False,
)
```

The description provides human-readable information about the collection.

Setting `enable_dynamic_field=False` means that inserted entities may only
contain fields explicitly defined in the schema. Unexpected fields are not
accepted.

## Creating the Collection

The collection is created with the schema:

```python
collection = Collection(
    name=COLLECTION_NAME,
    schema=schema,
    using=MILVUS_ALIAS,
)
```

Creating a collection defines its structure, but it does not insert any
entities and does not automatically create a vector index.

Immediately after creation, the number of entities is therefore:

```text
0
```

## Inspecting the Schema

The example prints each field in the collection:

```python
for field in collection.schema.fields:
    print(f"- {field.name}: {field.dtype}")
```

PyMilvus may display the field types using their internal numeric values:

```text
id: 5
label: 21
embedding: 101
```

These values represent:

| Numeric value | PyMilvus data type |
|---:|---|
| `5` | `INT64` |
| `21` | `VARCHAR` |
| `101` | `FLOAT_VECTOR` |

## Disconnecting from Milvus

The connection is closed in a `finally` block:

```python
finally:
    connections.disconnect(MILVUS_ALIAS)
```

The `finally` block runs whether the operation succeeds or fails, ensuring that
the client connection is properly closed.

## Running the Example

Make sure the virtual environment is active and the Milvus services are
running:

```bash
source .venv/bin/activate
docker compose up -d --pull never
```

Run the collection example:

```bash
python examples/02_create_collection.py
```

During the first execution, the expected result includes:

```text
Collection created successfully: learning_vectors
Number of entities: 0
```

During later executions, the program detects the existing collection:

```text
Collection already exists: learning_vectors
Number of entities: 0
```

## Important Notes

- A collection must have a primary-key field.
- Vector dimensions are fixed when the collection is created.
- Inserted vectors must match the configured dimension.
- A vector index is created separately after data insertion.
- A collection normally needs to be loaded before vector search.
- Changing an existing schema usually requires creating a new collection and
  migrating the data.

## Next Step

The collection is now ready to receive entities. The next example,
`examples/03_insert_vectors.py`, will insert identifiers, labels, and vectors
into `learning_vectors`.
