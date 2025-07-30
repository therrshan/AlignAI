"""
Pinecone setup script for the AI Resume Feedback Tool
Run this once to initialize your vector database indexes
"""

import os
import time
from pinecone import Pinecone, ServerlessSpec
from config.settings import (
    PINECONE_API_KEY, 
    PINECONE_ENVIRONMENT,
    RESUME_INDEX_NAME,
    PROJECTS_INDEX_NAME,
    EMBEDDING_DIMENSION
)

def setup_pinecone():
    """Initialize Pinecone indexes for resumes and projects"""
    
    if not PINECONE_API_KEY:
        raise ValueError("PINECONE_API_KEY not found in environment variables")
    
    # Initialize Pinecone
    pc = Pinecone(api_key=PINECONE_API_KEY)
    
    # Check existing indexes
    existing_indexes = [index.name for index in pc.list_indexes()]
    
    # Setup Resume Index
    if RESUME_INDEX_NAME not in existing_indexes:
        print(f"Creating {RESUME_INDEX_NAME} index...")
        pc.create_index(
            name=RESUME_INDEX_NAME,
            dimension=EMBEDDING_DIMENSION,
            metric='cosine',
            spec=ServerlessSpec(
                cloud='aws',
                region='us-east-1'
            )
        )
        print(f"✅ {RESUME_INDEX_NAME} index created successfully")
    else:
        print(f"ℹ️  {RESUME_INDEX_NAME} index already exists")
    
    # Setup Projects Index  
    if PROJECTS_INDEX_NAME not in existing_indexes:
        print(f"Creating {PROJECTS_INDEX_NAME} index...")
        pc.create_index(
            name=PROJECTS_INDEX_NAME,
            dimension=EMBEDDING_DIMENSION,
            metric='cosine',
            spec=ServerlessSpec(
                cloud='aws',
                region='us-east-1'
            )
        )
        print(f"✅ {PROJECTS_INDEX_NAME} index created successfully")
    else:
        print(f"ℹ️  {PROJECTS_INDEX_NAME} index already exists")
    
    # Wait for indexes to be ready
    print("Waiting for indexes to be ready...")
    for index_name in [RESUME_INDEX_NAME, PROJECTS_INDEX_NAME]:
        while not pc.describe_index(index_name).status['ready']:
            time.sleep(1)
    
    print("🎉 Pinecone setup completed successfully!")
    
    # Verify setup
    verify_setup(pc)

def verify_setup(pc):
    """Verify that indexes are properly configured"""
    print("\nVerifying setup...")
    
    for index_name in [RESUME_INDEX_NAME, PROJECTS_INDEX_NAME]:
        try:
            index_info = pc.describe_index(index_name)
            print(f"✅ {index_name}:")
            print(f"   - Dimension: {index_info.dimension}")
            print(f"   - Metric: {index_info.metric}")
            print(f"   - Status: {index_info.status['ready']}")
            
            # Test connection
            index = pc.Index(index_name)
            stats = index.describe_index_stats()
            print(f"   - Vector count: {stats['total_vector_count']}")
            
        except Exception as e:
            print(f"❌ Error with {index_name}: {e}")

def delete_indexes():
    """Helper function to delete indexes (use with caution!)"""
    pc = Pinecone(api_key=PINECONE_API_KEY)
    
    for index_name in [RESUME_INDEX_NAME, PROJECTS_INDEX_NAME]:
        try:
            pc.delete_index(index_name)
            print(f"🗑️  Deleted {index_name}")
        except Exception as e:
            print(f"Error deleting {index_name}: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Setup Pinecone indexes")
    parser.add_argument("--delete", action="store_true", help="Delete existing indexes")
    parser.add_argument("--reset", action="store_true", help="Delete and recreate indexes")
    
    args = parser.parse_args()
    
    if args.delete:
        delete_indexes()
    elif args.reset:
        delete_indexes()
        time.sleep(5)  # Wait for deletion to complete
        setup_pinecone()
    else:
        setup_pinecone()