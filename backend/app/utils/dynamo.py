"""
DynamoDB utilities for evidence metadata

Mock implementation for local development.
TODO: Replace with boto3 when AWS DynamoDB is configured.

Migration Guide:
1. Uncomment boto3 imports and client initialization
2. Replace mock storage with real DynamoDB operations
3. No changes needed in service or API layers
"""

from typing import List, Dict, Optional
from datetime import datetime, timezone
from app.core.config import settings

# TODO: Uncomment when AWS is configured
# import boto3
# from botocore.exceptions import ClientError

# Mock in-memory storage for local development
# TODO: Remove this when switching to real DynamoDB
_mock_evidence_store: Dict[str, Dict] = {}


def get_evidence_by_case(case_id: str) -> List[Dict]:
    """
    Get all evidence metadata for a case from DynamoDB

    Args:
        case_id: Case ID (DynamoDB partition key)

    Returns:
        List of evidence metadata dictionaries
    """
    # TODO: Replace with boto3 when AWS is configured
    # dynamodb = boto3.client('dynamodb', region_name=settings.AWS_REGION)
    # try:
    #     response = dynamodb.query(
    #         TableName=settings.DDB_EVIDENCE_TABLE,
    #         KeyConditionExpression='case_id = :case_id',
    #         ExpressionAttributeValues={
    #             ':case_id': {'S': case_id}
    #         }
    #     )
    #     items = response.get('Items', [])
    #     return [_deserialize_dynamodb_item(item) for item in items]
    # except ClientError as e:
    #     logger.error(f"DynamoDB query error: {e}")
    #     raise

    # Mock implementation
    evidence_list = [
        evidence for evidence in _mock_evidence_store.values()
        if evidence.get('case_id') == case_id
    ]

    # Sort by created_at descending (newest first)
    evidence_list.sort(key=lambda x: x.get('created_at', ''), reverse=True)

    return evidence_list


def get_evidence_by_id(evidence_id: str) -> Optional[Dict]:
    """
    Get evidence metadata by evidence ID from DynamoDB

    Args:
        evidence_id: Evidence ID (DynamoDB sort key)

    Returns:
        Evidence metadata dictionary or None if not found
    """
    # TODO: Replace with boto3 when AWS is configured
    # dynamodb = boto3.client('dynamodb', region_name=settings.AWS_REGION)
    # try:
    #     # Note: In real implementation, we need to scan or maintain a GSI
    #     # since evidence_id is not the partition key
    #     response = dynamodb.scan(
    #         TableName=settings.DDB_EVIDENCE_TABLE,
    #         FilterExpression='evidence_id = :evidence_id',
    #         ExpressionAttributeValues={
    #             ':evidence_id': {'S': evidence_id}
    #         }
    #     )
    #     items = response.get('Items', [])
    #     if not items:
    #         return None
    #     return _deserialize_dynamodb_item(items[0])
    # except ClientError as e:
    #     logger.error(f"DynamoDB scan error: {e}")
    #     raise

    # Mock implementation
    return _mock_evidence_store.get(evidence_id)


def put_evidence_metadata(evidence_data: Dict) -> Dict:
    """
    Insert or update evidence metadata in DynamoDB

    This is typically called by AI Worker, not backend API.
    Backend is read-only for evidence metadata.

    Args:
        evidence_data: Evidence metadata dictionary

    Returns:
        Stored evidence metadata
    """
    # TODO: Replace with boto3 when AWS is configured
    # dynamodb = boto3.client('dynamodb', region_name=settings.AWS_REGION)
    # try:
    #     item = _serialize_to_dynamodb(evidence_data)
    #     dynamodb.put_item(
    #         TableName=settings.DDB_EVIDENCE_TABLE,
    #         Item=item
    #     )
    #     return evidence_data
    # except ClientError as e:
    #     logger.error(f"DynamoDB put_item error: {e}")
    #     raise

    # Mock implementation
    evidence_id = evidence_data.get('id')
    if not evidence_id:
        raise ValueError("Evidence data must have 'id' field")

    # Add timestamp if not present
    if 'created_at' not in evidence_data:
        evidence_data['created_at'] = datetime.now(timezone.utc).isoformat()

    _mock_evidence_store[evidence_id] = evidence_data
    return evidence_data


def delete_evidence_metadata(evidence_id: str, case_id: str) -> bool:
    """
    Delete evidence metadata from DynamoDB

    Args:
        evidence_id: Evidence ID (sort key)
        case_id: Case ID (partition key)

    Returns:
        True if deleted, False if not found
    """
    # TODO: Replace with boto3 when AWS is configured
    # dynamodb = boto3.client('dynamodb', region_name=settings.AWS_REGION)
    # try:
    #     dynamodb.delete_item(
    #         TableName=settings.DDB_EVIDENCE_TABLE,
    #         Key={
    #             'case_id': {'S': case_id},
    #             'evidence_id': {'S': evidence_id}
    #         }
    #     )
    #     return True
    # except ClientError as e:
    #     logger.error(f"DynamoDB delete_item error: {e}")
    #     return False

    # Mock implementation
    if evidence_id in _mock_evidence_store:
        del _mock_evidence_store[evidence_id]
        return True
    return False


def clear_case_evidence(case_id: str) -> int:
    """
    Delete all evidence for a case (used when case is deleted)

    Args:
        case_id: Case ID

    Returns:
        Number of evidence items deleted
    """
    # TODO: Replace with boto3 when AWS is configured
    # dynamodb = boto3.client('dynamodb', region_name=settings.AWS_REGION)
    # try:
    #     response = dynamodb.query(
    #         TableName=settings.DDB_EVIDENCE_TABLE,
    #         KeyConditionExpression='case_id = :case_id',
    #         ExpressionAttributeValues={':case_id': {'S': case_id}}
    #     )
    #     items = response.get('Items', [])
    #     for item in items:
    #         dynamodb.delete_item(
    #             TableName=settings.DDB_EVIDENCE_TABLE,
    #             Key={
    #                 'case_id': {'S': case_id},
    #                 'evidence_id': item['evidence_id']
    #             }
    #         )
    #     return len(items)
    # except ClientError as e:
    #     logger.error(f"DynamoDB clear_case_evidence error: {e}")
    #     raise

    # Mock implementation
    evidence_to_delete = [
        eid for eid, evidence in _mock_evidence_store.items()
        if evidence.get('case_id') == case_id
    ]

    for eid in evidence_to_delete:
        del _mock_evidence_store[eid]

    return len(evidence_to_delete)


# TODO: Uncomment when AWS is configured
# def _serialize_to_dynamodb(data: Dict) -> Dict:
#     """Convert Python dict to DynamoDB item format"""
#     # Convert each value to DynamoDB type
#     # Example: {'id': 'ev_123'} -> {'id': {'S': 'ev_123'}}
#     pass
#
# def _deserialize_dynamodb_item(item: Dict) -> Dict:
#     """Convert DynamoDB item to Python dict"""
#     # Convert DynamoDB types to Python types
#     # Example: {'id': {'S': 'ev_123'}} -> {'id': 'ev_123'}
#     pass
