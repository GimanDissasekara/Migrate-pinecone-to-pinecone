# Pinecone Vector Database Migration Tool

This tool helps you migrate all vectors and their metadata from a Pinecone vector database to a new vector database of your choice. The tool currently supports migration to:

1. Another Pinecone index
2. ChromaDB collection
3. FAISS index

## Prerequisites

Install the required dependencies:

```bash
pip install pinecone-client tqdm
```

Depending on your target vector database, you may need additional packages:

- For ChromaDB: `pip install chromadb`
- For FAISS: `pip install faiss-cpu numpy` (or `faiss-gpu` for GPU support)

## Usage

The migration tool is a command-line application with various options:

### Basic Usage

```bash
python pinecone_migration.py --pinecone-api-key YOUR_API_KEY --pinecone-env YOUR_ENV --source-index SOURCE_INDEX_NAME --target-db TARGET_DB_TYPE --target-name TARGET_NAME
```

### Required Arguments

- `--pinecone-api-key`: Your Pinecone API key
- `--pinecone-env`: Your Pinecone environment (e.g., us-east1-gcp)
- `--source-index`: The name of your source Pinecone index
- `--target-db`: The type of target database (`pinecone`, `chroma`, or `faiss`)

### Target-Specific Arguments

#### For Pinecone Target

```bash
python pinecone_migration.py --pinecone-api-key YOUR_API_KEY --pinecone-env YOUR_ENV --source-index SOURCE_INDEX --target-db pinecone --target-name NEW_INDEX_NAME --dimension VECTOR_DIMENSION --metric DISTANCE_METRIC
```

- `--target-name`: Name for the new Pinecone index
- `--dimension`: Vector dimension (required for new Pinecone index)
- `--metric`: Distance metric (default: 'cosine', options: 'cosine', 'euclidean', 'dotproduct')

#### For ChromaDB Target

```bash
python pinecone_migration.py --pinecone-api-key YOUR_API_KEY --pinecone-env YOUR_ENV --source-index SOURCE_INDEX --target-db chroma --target-name COLLECTION_NAME --persist-dir PERSIST_DIRECTORY
```

- `--target-name`: Name for the ChromaDB collection
- `--persist-dir`: Directory to persist the ChromaDB data (optional)

#### For FAISS Target

```bash
python pinecone_migration.py --pinecone-api-key YOUR_API_KEY --pinecone-env YOUR_ENV --source-index SOURCE_INDEX --target-db faiss --index-file-path PATH_TO_SAVE_INDEX
```

- `--index-file-path`: File path to save the FAISS index

## Examples

### Migrate to a new Pinecone index

```bash
python pinecone_migration.py --pinecone-api-key abcd1234 --pinecone-env us-east1-gcp --source-index my-old-index --target-db pinecone --target-name my-new-index --dimension 768 --metric cosine
```

### Migrate to ChromaDB

```bash
python pinecone_migration.py --pinecone-api-key abcd1234 --pinecone-env us-east1-gcp --source-index my-index --target-db chroma --target-name my-collection --persist-dir ./chroma_data
```

### Migrate to FAISS

```bash
python pinecone_migration.py --pinecone-api-key abcd1234 --pinecone-env us-east1-gcp --source-index my-index --target-db faiss --index-file-path ./my_faiss_index.idx
```

## Notes

- The migration process retrieves all vectors and metadata from the source Pinecone index in batches to avoid memory issues.
- For large indexes, the migration may take some time. Progress bars will show the status of each step.
- FAISS only stores vectors, not metadata or IDs. The tool saves a separate JSON file with metadata and IDs alongside the FAISS index.
- Make sure you have sufficient disk space and memory for large migrations.

## Troubleshooting

- If you encounter timeout errors with Pinecone, you might need to adjust the batch sizes in the code.
- For very large indexes, consider running the migration in multiple steps or on a machine with more memory.
"# Migrate-pinecone-to-pinecone" 
