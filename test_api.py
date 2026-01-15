"""
Test script for Vector Database API

Run the API first: uvicorn app.main:app --reload
Then run: python test_api.py
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json"}


def test_health():
    """Test health endpoint."""
    print("\n=== Testing Health Check ===")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200


def test_root():
    """Test root endpoint."""
    print("\n=== Testing Root Endpoint ===")
    response = requests.get(f"{BASE_URL}/")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200


def test_index():
    """Test indexing chunks."""
    print("\n=== Testing Index Endpoint ===")
    
    chunks = {
        "chunks": [
            {
                "chunk_id": "invoice_001_0",
                "document_id": "invoice_001",
                "user_id": "user_001",
                "content": "Invoice #INV-2026-001\nDate: January 15, 2026\nAmount: $1500.00\nClient: Acme Corporation\nDescription: Professional Services",
                "metadata": {
                    "source": "pdf",
                    "page_number": 1,
                    "chunk_index": 0,
                    "created_at": datetime.utcnow().isoformat(),
                    "tags": ["invoice", "financial", "2026"]
                }
            },
            {
                "chunk_id": "invoice_001_1",
                "document_id": "invoice_001",
                "user_id": "user_001",
                "content": "Payment Terms: Net 30 days\nBilling Address: 123 Main St, City, State 12345\nEmail: contact@acme.com\nPhone: (555) 123-4567",
                "metadata": {
                    "source": "pdf",
                    "page_number": 1,
                    "chunk_index": 1,
                    "created_at": datetime.utcnow().isoformat(),
                    "tags": ["invoice", "contact"]
                }
            },
            {
                "chunk_id": "medical_001_0",
                "document_id": "medical_001",
                "user_id": "user_002",
                "content": "Medical Record - Patient ID: MR-2026-001\nDate of Visit: January 10, 2026\nPatient Name: John Doe\nDiagnosis: Hypertension\nPrescription: Lisinopril 10mg daily",
                "metadata": {
                    "source": "ocr",
                    "page_number": 1,
                    "chunk_index": 0,
                    "created_at": datetime.utcnow().isoformat(),
                    "tags": ["medical", "healthcare", "prescription"]
                }
            }
        ]
    }
    
    response = requests.post(f"{BASE_URL}/vector/index", json=chunks, headers=HEADERS)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200


def test_semantic_search():
    """Test semantic search."""
    print("\n=== Testing Semantic Search ===")
    
    search_request = {
        "query": "What is the invoice amount and payment terms?",
        "top_k": 5
    }
    
    response = requests.post(
        f"{BASE_URL}/vector/search/semantic",
        json=search_request,
        headers=HEADERS
    )
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Query Time: {result.get('query_time_ms')} ms")
    print(f"Total Results: {result.get('total_results')}")
    
    if result.get('results'):
        print("\nTop Result:")
        top = result['results'][0]
        print(f"  Content: {top['content'][:100]}...")
        print(f"  Similarity Score: {top['similarity_score']}")
        print(f"  Tags: {top['metadata']['tags']}")
    
    return response.status_code == 200


def test_metadata_search():
    """Test metadata-filtered search."""
    print("\n=== Testing Metadata Search ===")
    
    search_request = {
        "filters": {
            "source": "pdf",
            "tags": ["invoice"]
        },
        "top_k": 5
    }
    
    response = requests.post(
        f"{BASE_URL}/vector/search/metadata",
        json=search_request,
        headers=HEADERS
    )
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Total Results: {result.get('total_results')}")
    print(f"Query Time: {result.get('query_time_ms')} ms")
    
    if result.get('results'):
        print("\nMatching Chunks:")
        for i, res in enumerate(result['results'], 1):
            print(f"  {i}. {res['chunk_id']} - Tags: {res['metadata']['tags']}")
    
    return response.status_code == 200


def test_hybrid_search():
    """Test hybrid search."""
    print("\n=== Testing Hybrid Search ===")
    
    search_request = {
        "query": "financial transaction payment",
        "filters": {
            "source": "pdf",
            "tags": ["financial"]
        },
        "top_k": 5,
        "weight_vector": 0.7
    }
    
    response = requests.post(
        f"{BASE_URL}/vector/search/hybrid",
        json=search_request,
        headers=HEADERS
    )
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Total Results: {result.get('total_results')}")
    print(f"Query Time: {result.get('query_time_ms')} ms")
    
    if result.get('results'):
        print("\nHybrid Results:")
        for i, res in enumerate(result['results'], 1):
            print(f"  {i}. {res['chunk_id']}")
            print(f"     Score: {res['similarity_score']}")
            print(f"     Source: {res['metadata']['source']}")
    
    return response.status_code == 200


def test_stats():
    """Test statistics endpoint."""
    print("\n=== Testing Statistics Endpoint ===")
    
    response = requests.get(f"{BASE_URL}/vector/stats")
    print(f"Status: {response.status_code}")
    stats = response.json()
    
    print(f"Total Chunks: {stats['total_chunks']}")
    print(f"Total Documents: {stats['total_documents']}")
    print(f"Total Users: {stats['total_users']}")
    print(f"Embedding Model: {stats['embedding_model']}")
    print(f"Embedding Dimension: {stats['embedding_dimension']}")
    print(f"Chunk Size: {stats['chunk_size']}")
    print(f"Chunk Overlap: {stats['chunk_overlap']}")
    
    return response.status_code == 200


def test_error_handling():
    """Test error handling."""
    print("\n=== Testing Error Handling ===")
    
    # Test empty query
    print("\n1. Testing empty query:")
    search_request = {"query": "", "top_k": 5}
    response = requests.post(f"{BASE_URL}/vector/search/semantic", json=search_request)
    print(f"   Status: {response.status_code}")
    if response.status_code != 200:
        print(f"   Error: {response.json()}")
    
    # Test invalid top_k
    print("\n2. Testing invalid top_k:")
    search_request = {"query": "test", "top_k": -1}
    response = requests.post(f"{BASE_URL}/vector/search/semantic", json=search_request)
    print(f"   Status: {response.status_code}")
    if response.status_code != 200:
        print(f"   Error: {response.json()}")
    
    # Test missing required field
    print("\n3. Testing missing required field:")
    search_request = {"top_k": 5}
    response = requests.post(f"{BASE_URL}/vector/search/semantic", json=search_request)
    print(f"   Status: {response.status_code}")


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("Vector Database API Test Suite")
    print("=" * 60)
    
    tests = [
        ("Health Check", test_health),
        ("Root Endpoint", test_root),
        ("Index Chunks", test_index),
        ("Semantic Search", test_semantic_search),
        ("Metadata Search", test_metadata_search),
        ("Hybrid Search", test_hybrid_search),
        ("Statistics", test_stats),
        ("Error Handling", test_error_handling),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"ERROR: {str(e)}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")


if __name__ == "__main__":
    try:
        run_all_tests()
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to API at http://localhost:8000")
        print("Please ensure the server is running: uvicorn app.main:app --reload")
