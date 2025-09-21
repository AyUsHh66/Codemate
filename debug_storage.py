"""
Debug script to check the status of your storage files and help diagnose issues.
Run this after ingestion to see what's actually stored.
"""

import json
import os
import sys
from pathlib import Path

def check_storage_status():
    """Check the status of all storage files."""
    storage_dir = "./storage"
    
    print("=" * 60)
    print("STORAGE STATUS CHECK")
    print("=" * 60)
    
    # Check if storage directory exists
    if not os.path.exists(storage_dir):
        print(f"❌ Storage directory '{storage_dir}' does not exist!")
        print("   Run 'python ingestion.py' first.")
        return
    
    print(f"✓ Storage directory exists: {storage_dir}\n")
    
    # Expected files
    files_to_check = [
        "docstore.json",
        "index_store.json", 
        "graph_store.json",
        "image__vector_store.json"
    ]
    
    for filename in files_to_check:
        filepath = os.path.join(storage_dir, filename)
        print(f"\n📄 {filename}:")
        print("-" * 40)
        
        if not os.path.exists(filepath):
            print(f"   ❌ File does not exist!")
            continue
            
        # Get file size
        size = os.path.getsize(filepath)
        print(f"   Size: {size:,} bytes")
        
        if size < 10:
            print(f"   ⚠️  File appears to be empty!")
            continue
        
        # Try to load and analyze JSON content
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if filename == "docstore.json":
                # Check docstore structure
                if "docstore/data" in data:
                    doc_count = len(data["docstore/data"])
                    print(f"   ✓ Contains {doc_count} documents")
                    if doc_count == 0:
                        print(f"   ⚠️  No documents in docstore!")
                    else:
                        # Show first document ID as sample
                        first_id = list(data["docstore/data"].keys())[0]
                        print(f"   Sample doc ID: {first_id[:50]}...")
                else:
                    print(f"   ⚠️  Unexpected structure - no 'docstore/data' key")
                    print(f"   Keys found: {list(data.keys())}")
            
            elif filename == "index_store.json":
                if "index_store/data" in data:
                    index_count = len(data["index_store/data"])
                    print(f"   ✓ Contains {index_count} index entries")
                else:
                    print(f"   ⚠️  Unexpected structure")
            
            else:
                # For other files, just show basic info
                print(f"   ✓ Valid JSON with {len(data)} top-level keys")
                
        except json.JSONDecodeError as e:
            print(f"   ❌ Invalid JSON: {e}")
        except Exception as e:
            print(f"   ❌ Error reading file: {e}")
    
    # Check Qdrant database
    print(f"\n\n🗄️  Qdrant Database:")
    print("-" * 40)
    qdrant_path = os.path.join(storage_dir, "qdrant_db")
    if os.path.exists(qdrant_path):
        print(f"   ✓ Qdrant directory exists")
        # Count subdirectories/files
        items = list(Path(qdrant_path).iterdir())
        print(f"   Contains {len(items)} items")
    else:
        print(f"   ❌ Qdrant directory does not exist!")
    
    # Check data directory
    print(f"\n\n📁 Data Directory:")
    print("-" * 40)
    data_dir = "./data"
    if os.path.exists(data_dir):
        files = list(Path(data_dir).glob("**/*"))
        file_count = sum(1 for f in files if f.is_file())
        print(f"   ✓ Found {file_count} files in data directory")
        for f in files[:5]:  # Show first 5 files
            if f.is_file():
                print(f"     - {f.name}")
    else:
        print(f"   ❌ Data directory does not exist!")
    
    print("\n" + "=" * 60)
    print("RECOMMENDATIONS:")
    print("=" * 60)
    
    # Provide recommendations based on findings
    if not os.path.exists(os.path.join(storage_dir, "docstore.json")):
        print("1. Run 'python ingestion.py' to create the storage files")
    else:
        try:
            with open(os.path.join(storage_dir, "docstore.json"), 'r') as f:
                data = json.load(f)
                if "docstore/data" not in data or len(data.get("docstore/data", {})) == 0:
                    print("1. Re-run 'python ingestion.py' - the docstore is empty")
                    print("2. Make sure you have PDF files in the ./data directory")
                    print("3. Check that the PDFs are readable and not corrupted")
        except:
            print("1. The docstore.json file is corrupted - delete ./storage and re-run ingestion")

if __name__ == "__main__":
    check_storage_status()