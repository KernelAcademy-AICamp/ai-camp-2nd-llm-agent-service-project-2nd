"""
Qdrant 연결 상태 확인 스크립트
"""
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from qdrant_client import QdrantClient

def main():
    url = os.getenv('QDRANT_URL')
    api_key = os.getenv('QDRANT_API_KEY')

    print('=== Qdrant Connection Test ===')
    print(f'URL: {url[:50]}...' if url else 'URL: None')
    print()

    try:
        client = QdrantClient(url=url, api_key=api_key, timeout=30)
        collections = client.get_collections()

        print('Connection: SUCCESS')
        print(f'Collections found: {len(collections.collections)}')
        print()

        for col in collections.collections:
            info = client.get_collection(col.name)
            print(f'  - {col.name}')
            print(f'    Vectors: {info.points_count}')
            print(f'    Status: {info.status}')
            print()

        # Check legal_templates content
        print('=== legal_templates 상세 ===')
        try:
            result = client.scroll(
                collection_name='legal_templates',
                limit=10,
                with_payload=True,
                with_vectors=False
            )
            for point in result[0]:
                print(f'  Point ID: {point.id}')
                payload = point.payload or {}
                print(f'    Type: {payload.get("template_type", "N/A")}')
                print(f'    Name: {payload.get("template_name", "N/A")}')
                print()
        except Exception as e:
            print(f'  Error: {e}')

    except Exception as e:
        print('Connection: FAILED')
        print(f'Error: {e}')
        return 1

    return 0

if __name__ == '__main__':
    sys.exit(main())
