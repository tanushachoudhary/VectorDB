"""
Test document upload functionality

Run: python test_upload.py
"""

import requests
import os
from pathlib import Path

BASE_URL = "http://localhost:8000"


def create_test_files():
    """Create test files for upload."""
    test_dir = Path("test_files")
    test_dir.mkdir(exist_ok=True)
    
    # Create a test text file
    text_file = test_dir / "sample_invoice.txt"
    text_file.write_text("""
    INVOICE
    
    Invoice Number: INV-2026-001
    Date: January 15, 2026
    
    Bill To:
    Acme Corporation
    123 Main Street
    City, State 12345
    
    Description: Professional Services - January 2026
    Amount: $5,000.00
    Tax (10%): $500.00
    Total: $5,500.00
    
    Payment Terms: Net 30 days
    Due Date: February 15, 2026
    
    Contact: billing@company.com
    Phone: (555) 123-4567
    """)
    
    return {"text": text_file}


def test_upload_text_file():
    """Test uploading a text file."""
    print("\n=== Testing Text File Upload ===")
    
    test_files = create_test_files()
    
    with open(test_files["text"], "rb") as f:
        files = {"file": ("sample_invoice.txt", f, "text/plain")}
        data = {
            "user_id": "user_001",
            "tags": "invoice,financial,2026"
        }
        
        response = requests.post(
            f"{BASE_URL}/vector/upload",
            files=files,
            data=data
        )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Success!")
        print(f"   Document ID: {result['document_id']}")
        print(f"   Filename: {result['filename']}")
        print(f"   Source: {result['source']}")
        print(f"   Total Pages: {result['total_pages']}")
        print(f"   Total Chunks: {result['total_chunks']}")
        print(f"   Extraction Time: {result['extraction_time_ms']}ms")
        print(f"   Indexing Time: {result['indexing_time_ms']}ms")
        print(f"   First Chunk ID: {result['chunk_ids'][0]}")
        return result['document_id']
    else:
        print(f"❌ Failed: {response.text}")
        return None


def test_search_uploaded_document(document_id=None):
    """Test searching the uploaded document."""
    print("\n=== Testing Search on Uploaded Document ===")
    
    # Semantic search
    search_request = {
        "query": "What is the invoice amount and due date?",
        "top_k": 3
    }
    
    response = requests.post(
        f"{BASE_URL}/vector/search/semantic",
        json=search_request
    )
    
    if response.status_code == 200:
        results = response.json()
        print(f"✅ Found {results['total_results']} results")
        print(f"   Query time: {results['query_time_ms']}ms")
        
        if results['results']:
            top = results['results'][0]
            print(f"\n   Top Result:")
            print(f"   - Chunk ID: {top['chunk_id']}")
            print(f"   - Score: {top['similarity_score']}")
            print(f"   - Content: {top['content'][:100]}...")
            print(f"   - Tags: {top['metadata']['tags']}")
    else:
        print(f"❌ Search failed: {response.text}")


def test_metadata_filter():
    """Test metadata filtering."""
    print("\n=== Testing Metadata Filter ===")
    
    search_request = {
        "filters": {
            "source": "text",
            "tags": ["invoice"]
        },
        "top_k": 10
    }
    
    response = requests.post(
        f"{BASE_URL}/vector/search/metadata",
        json=search_request
    )
    
    if response.status_code == 200:
        results = response.json()
        print(f"✅ Found {results['total_results']} invoice documents")
        
        for i, r in enumerate(results['results'][:3], 1):
            print(f"   {i}. {r['chunk_id']} - Tags: {r['metadata']['tags']}")
    else:
        print(f"❌ Filter failed: {response.text}")


def test_hybrid_search():
    """Test hybrid search."""
    print("\n=== Testing Hybrid Search ===")
    
    search_request = {
        "query": "payment terms contact information",
        "filters": {
            "tags": ["invoice"]
        },
        "top_k": 5,
        "weight_vector": 0.7
    }
    
    response = requests.post(
        f"{BASE_URL}/vector/search/hybrid",
        json=search_request
    )
    
    if response.status_code == 200:
        results = response.json()
        print(f"✅ Found {results['total_results']} results")
        print(f"   Query time: {results['query_time_ms']}ms")
        
        for i, r in enumerate(results['results'], 1):
            print(f"   {i}. Score: {r['similarity_score']:.4f} - {r['chunk_id']}")
    else:
        print(f"❌ Hybrid search failed: {response.text}")


def test_stats():
    """Test stats endpoint."""
    print("\n=== Testing Stats ===")
    
    response = requests.get(f"{BASE_URL}/vector/stats")
    
    if response.status_code == 200:
        stats = response.json()
        print(f"✅ Database Statistics:")
        print(f"   Total Chunks: {stats['total_chunks']}")
        print(f"   Total Documents: {stats['total_documents']}")
        print(f"   Total Users: {stats['total_users']}")
        print(f"   Model: {stats['embedding_model']}")
    else:
        print(f"❌ Stats failed: {response.text}")


def run_upload_tests():
    """Run all upload tests."""
    print("=" * 60)
    print("Document Upload Test Suite")
    print("=" * 60)
    
    try:
        # Test upload
        document_id = test_upload_text_file()
        
        if document_id:
            # Test searches
            test_search_uploaded_document(document_id)
            test_metadata_filter()
            test_hybrid_search()
            test_stats()
        
        print("\n" + "=" * 60)
        print("All tests completed!")
        print("=" * 60)
    
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to API at http://localhost:8000")
        print("Please ensure the server is running: uvicorn app.main:app --reload")
    
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")


if __name__ == "__main__":
    run_upload_tests()
