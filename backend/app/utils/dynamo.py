"""
DynamoDB utilities for evidence metadata

Real boto3 implementation for AWS DynamoDB.

Table Schema:
- Table: leh_evidence
- PK: evidence_id (HASH)
- GSI: case_id-index (case_id as HASH, ProjectionType: ALL)
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError

from app.core.config import settings

logger = logging.getLogger(__name__)

# Initialize DynamoDB client
_dynamodb_client = None


def _get_dynamodb_client():
    """Get or create DynamoDB client (singleton pattern)"""
    global _dynamodb_client
    if _dynamodb_client is None:
        _dynamodb_client = boto3.client(
            'dynamodb',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
    return _dynamodb_client


def _serialize_value(value) -> Dict:
    """Convert Python value to DynamoDB type"""
    if value is None:
        return {'NULL': True}
    elif isinstance(value, bool):
        return {'BOOL': value}
    elif isinstance(value, str):
        return {'S': value}
    elif isinstance(value, (int, float)):
        return {'N': str(value)}
    elif isinstance(value, list):
        if not value:
            return {'L': []}
        return {'L': [_serialize_value(v) for v in value]}
    elif isinstance(value, dict):
        return {'M': {k: _serialize_value(v) for k, v in value.items()}}
    else:
        return {'S': str(value)}


def _deserialize_value(dynamodb_value: Dict):
    """Convert DynamoDB type to Python value"""
    if 'NULL' in dynamodb_value:
        return None
    elif 'BOOL' in dynamodb_value:
        return dynamodb_value['BOOL']
    elif 'S' in dynamodb_value:
        return dynamodb_value['S']
    elif 'N' in dynamodb_value:
        num_str = dynamodb_value['N']
        return float(num_str) if '.' in num_str else int(num_str)
    elif 'L' in dynamodb_value:
        return [_deserialize_value(v) for v in dynamodb_value['L']]
    elif 'M' in dynamodb_value:
        return {k: _deserialize_value(v) for k, v in dynamodb_value['M'].items()}
    elif 'SS' in dynamodb_value:
        return list(dynamodb_value['SS'])
    elif 'NS' in dynamodb_value:
        return [float(n) if '.' in n else int(n) for n in dynamodb_value['NS']]
    else:
        return None


def _serialize_to_dynamodb(data: Dict) -> Dict:
    """Convert Python dict to DynamoDB item format"""
    return {k: _serialize_value(v) for k, v in data.items()}


def _deserialize_dynamodb_item(item: Dict) -> Dict:
    """Convert DynamoDB item to Python dict"""
    return {k: _deserialize_value(v) for k, v in item.items()}


def get_evidence_by_case(case_id: str) -> List[Dict]:
    """
    Get all evidence metadata for a case from DynamoDB

    Uses GSI: case_id-index for efficient query

    Args:
        case_id: Case ID (GSI partition key)

    Returns:
        List of evidence metadata dictionaries
    """
    dynamodb = _get_dynamodb_client()

    try:
        response = dynamodb.query(
            TableName=settings.DDB_EVIDENCE_TABLE,
            IndexName='case_id-index',
            KeyConditionExpression='case_id = :case_id',
            ExpressionAttributeValues={
                ':case_id': {'S': case_id}
            }
        )

        items = response.get('Items', [])
        evidence_list = [_deserialize_dynamodb_item(item) for item in items]

        # Sort by created_at descending (newest first)
        evidence_list.sort(key=lambda x: x.get('created_at', ''), reverse=True)

        return evidence_list

    except ClientError as e:
        logger.error(f"DynamoDB query error for case {case_id}: {e}")
        raise


def get_evidence_by_id(evidence_id: str) -> Optional[Dict]:
    """
    Get evidence metadata by evidence ID from DynamoDB

    Args:
        evidence_id: Evidence ID (DynamoDB primary key)

    Returns:
        Evidence metadata dictionary or None if not found
    """
    dynamodb = _get_dynamodb_client()

    try:
        response = dynamodb.get_item(
            TableName=settings.DDB_EVIDENCE_TABLE,
            Key={
                'evidence_id': {'S': evidence_id}
            }
        )

        item = response.get('Item')
        if not item:
            return None

        return _deserialize_dynamodb_item(item)

    except ClientError as e:
        logger.error(f"DynamoDB get_item error for evidence {evidence_id}: {e}")
        raise


def put_evidence_metadata(evidence_data: Dict) -> Dict:
    """
    Insert or update evidence metadata in DynamoDB

    This is typically called by AI Worker, not backend API.
    Backend is read-only for evidence metadata.

    Args:
        evidence_data: Evidence metadata dictionary
            Required fields:
            - id or evidence_id: Evidence ID (will be stored as evidence_id)
            - case_id: Case ID

    Returns:
        Stored evidence metadata
    """
    dynamodb = _get_dynamodb_client()

    # Normalize evidence_id field
    evidence_id = evidence_data.get('evidence_id') or evidence_data.get('id')
    if not evidence_id:
        raise ValueError("Evidence data must have 'id' or 'evidence_id' field")

    # Prepare item data
    item_data = evidence_data.copy()
    item_data['evidence_id'] = evidence_id
    if 'id' in item_data and 'evidence_id' != 'id':
        item_data['id'] = evidence_id  # Keep id field for backward compatibility

    # Add timestamp if not present
    if 'created_at' not in item_data:
        item_data['created_at'] = datetime.now(timezone.utc).isoformat()

    try:
        dynamodb.put_item(
            TableName=settings.DDB_EVIDENCE_TABLE,
            Item=_serialize_to_dynamodb(item_data)
        )
        return item_data

    except ClientError as e:
        logger.error(f"DynamoDB put_item error for evidence {evidence_id}: {e}")
        raise


def delete_evidence_metadata(evidence_id: str, case_id: str = None) -> bool:
    """
    Delete evidence metadata from DynamoDB

    Args:
        evidence_id: Evidence ID (primary key)
        case_id: Case ID (not needed for delete since PK is evidence_id)

    Returns:
        True if deleted successfully
    """
    dynamodb = _get_dynamodb_client()

    try:
        dynamodb.delete_item(
            TableName=settings.DDB_EVIDENCE_TABLE,
            Key={
                'evidence_id': {'S': evidence_id}
            }
        )
        return True

    except ClientError as e:
        logger.error(f"DynamoDB delete_item error for evidence {evidence_id}: {e}")
        return False


def clear_case_evidence(case_id: str) -> int:
    """
    Delete all evidence for a case (used when case is deleted)

    Args:
        case_id: Case ID

    Returns:
        Number of evidence items deleted
    """
    dynamodb = _get_dynamodb_client()

    try:
        # First, query all evidence for this case using GSI
        response = dynamodb.query(
            TableName=settings.DDB_EVIDENCE_TABLE,
            IndexName='case_id-index',
            KeyConditionExpression='case_id = :case_id',
            ExpressionAttributeValues={
                ':case_id': {'S': case_id}
            },
            ProjectionExpression='evidence_id'  # Only need the key
        )

        items = response.get('Items', [])
        deleted_count = 0

        # Delete each evidence item
        for item in items:
            evidence_id = item['evidence_id']['S']
            try:
                dynamodb.delete_item(
                    TableName=settings.DDB_EVIDENCE_TABLE,
                    Key={
                        'evidence_id': {'S': evidence_id}
                    }
                )
                deleted_count += 1
            except ClientError as e:
                logger.warning(f"Failed to delete evidence {evidence_id}: {e}")

        return deleted_count

    except ClientError as e:
        logger.error(f"DynamoDB clear_case_evidence error for case {case_id}: {e}")
        raise
