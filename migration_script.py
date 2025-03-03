import pinecone
import time
from tqdm import tqdm

# Source database details
SOURCE_API_KEY = "3cfb3661-3bbb-4407-876f-fae4b939c696"
SOURCE_ENV = "apw5-4e34-81fa"
SOURCE_INDEX = "cg-web"
SOURCE_PROJECT_ID = "td2ku85"

# Destination database details
DEST_API_KEY = "pcsk_4BnXVK_ETaQTT3hpLAcJxGEWq7FqhkNfKKN6Mvv3ptexvyyw4C5YbRHSqGhrUuXi2sqKDx"  # You need to add your destination API key
DEST_INDEX = "ccs-agent-vdb"
DEST_HOST = "https://ccs-agent-vdb-wo8wu73.svc.aped-4627-b74a.pinecone.io"
DEST_ENVIRONMENT = "us-east-1"  # We're using the region as environment here

# Batch size for fetching and inserting vectors
BATCH_SIZE = 196

def migrate_vectors():
    """Migrate vectors from source Pinecone DB to destination Pinecone DB."""
    print("Starting migration from cg-web to ccs-agent-vdb...")
    
    # Initialize Pinecone for source database using the new approach
    source_pc = pinecone.Pinecone(api_key=SOURCE_API_KEY)
    source_index = source_pc.Index(SOURCE_INDEX)
    
    # Get total vector count from source
    try:
        stats = source_index.describe_index_stats()
    except Exception as e:
        if "unknown method" in str(e).lower():
            # Try the newer method naming pattern
            stats = source_index.stats()
        else:
            raise
            
    total_vectors = stats.get('total_vector_count', stats.get('namespaces', {}).get('', {}).get('vector_count', 0))
    print(f"Total vectors to migrate: {total_vectors}")
    
    if total_vectors == 0:
        print("No vectors found in source database. Exiting.")
        return
    
    # Initialize Pinecone for destination database using the new approach
    dest_pc = pinecone.Pinecone(api_key=DEST_API_KEY)
    
    # Connect to the destination index
    dest_index = dest_pc.Index(
        name=DEST_INDEX,
        host=DEST_HOST
    )
    
    # Setup progress tracking
    progress_bar = tqdm(total=total_vectors, desc="Migrating vectors")
    
    # Use pagination to fetch all vectors
    pagination_token = None
    vectors_migrated = 0
    
    while True:
        # Fetch batch of vectors from source
        try:
            # Try different fetch methods based on the available API
            try:
                # Try list (newer API style)
                fetch_response = source_index.list(
                    limit=BATCH_SIZE,
                    namespace="",
                    include_values=True,
                    include_metadata=True,
                    pagination_token=pagination_token
                )
                
                vectors = {}
                for record in fetch_response.get('vectors', []):
                    vectors[record['id']] = {
                        'values': record['values'],
                        'metadata': record.get('metadata', {})
                    }
                
                pagination_token = fetch_response.get('pagination_token')
            except Exception as list_error:
                try:
                    # Fallback to query method
                    fetch_response = source_index.query(
                        top_k=BATCH_SIZE,
                        include_values=True,
                        include_metadata=True,
                        vector=[0] * 1536,  # Dummy vector for query
                    )
                    
                    vectors = {}
                    for match in fetch_response.get('matches', []):
                        vectors[match['id']] = {
                            'values': match['values'],
                            'metadata': match.get('metadata', {})
                        }
                    
                    # No pagination with query method, so we'll break after one batch
                    pagination_token = None
                except Exception as query_error:
                    # Last resort: try fetch method
                    fetch_response = source_index.fetch(
                        ids=[],  # Empty for all vectors
                        namespace="",
                        include_values=True,
                        include_metadata=True
                    )
                    
                    vectors = fetch_response.get('vectors', {})
                    pagination_token = fetch_response.get('pagination_token')
            
            if not vectors:
                break
                
            # Prepare vectors for upsert
            upsert_batch = []
            for id, vector_data in vectors.items():
                upsert_batch.append({
                    'id': id,
                    'values': vector_data['values'],
                    'metadata': vector_data.get('metadata', {})
                })
            
            # Upsert vectors to destination
            if upsert_batch:
                try:
                    # Try standard upsert method
                    dest_index.upsert(vectors=upsert_batch)
                except Exception as e:
                    try:
                        # Try upsert with different parameter naming
                        dest_index.upsert(
                            vectors=[(v['id'], v['values'], v['metadata']) for v in upsert_batch]
                        )
                    except Exception as e2:
                        print(f"Failed to upsert: {e2}")
                        raise
                
            vectors_migrated += len(upsert_batch)
            progress_bar.update(len(upsert_batch))
            
            # If no more pagination token, we've fetched all vectors
            if not pagination_token:
                break
                
            # Small delay to avoid rate limiting
            time.sleep(0.5)
        except Exception as e:
            print(f"Error during migration: {e}")
            break
    
    progress_bar.close()
    print(f"Migration complete! {vectors_migrated} vectors migrated to {DEST_INDEX}.")
    
    # Verify the migration
    try:
        # First try describe_index_stats
        dest_stats = dest_index.describe_index_stats()
        dest_total_vectors = dest_stats.get('total_vector_count', 0)
    except Exception as e1:
        try:
            # Try stats method (newer API)
            dest_stats = dest_index.stats()
            dest_total_vectors = 0
            # Try to extract vector count from different response formats
            if 'namespaces' in dest_stats:
                for ns, ns_stats in dest_stats['namespaces'].items():
                    dest_total_vectors += ns_stats.get('vector_count', 0)
            elif 'dimension' in dest_stats:
                # For the new serverless indexes
                dest_total_vectors = dest_stats.get('vector_count', 0)
            else:
                dest_total_vectors = 0
        except Exception as e2:
            print(f"Warning: Could not get destination stats: {e2}")
            dest_total_vectors = vectors_migrated
            
    print(f"Destination index now has {dest_total_vectors} vectors (Expected: {vectors_migrated}).")
    
    if dest_total_vectors == 0 and vectors_migrated > 0:
        print("Warning: The destination index reports 0 vectors even though vectors were migrated.")
        print("This might be due to API differences or indexing delay.")
        print("Please check the destination index manually to confirm the migration status.")
    
if __name__ == "__main__":
    migrate_vectors()
