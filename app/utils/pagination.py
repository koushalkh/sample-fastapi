"""
Pagination utilities for cursor-based pagination with DynamoDB.
Provides encoding/decoding functionality for pagination cursors.
"""

import base64
import json
from typing import Optional, Dict, Any
from structlog import get_logger

logger = get_logger(__name__)


def encode_cursor(pagination_key: Optional[Dict[str, Any]]) -> Optional[str]:
    """
    Encode DynamoDB pagination key as a base64 cursor for client use.
    
    Args:
        pagination_key: DynamoDB last_evaluated_key or None
        
    Returns:
        Base64 encoded cursor string or None
    """
    if not pagination_key:
        return None
    
    try:
        # Convert to JSON string and encode as base64
        cursor_data = json.dumps(pagination_key, default=str, sort_keys=True)
        cursor_bytes = cursor_data.encode('utf-8')
        return base64.b64encode(cursor_bytes).decode('utf-8')
    except Exception as e:
        logger.warning("Failed to encode cursor", error=str(e))
        return None


def decode_cursor(cursor: Optional[str]) -> Optional[Dict[str, Any]]:
    """
    Decode base64 cursor back to DynamoDB pagination key.
    
    Args:
        cursor: Base64 encoded cursor string or None
        
    Returns:
        DynamoDB pagination key dict or None if invalid
    """
    if not cursor:
        return None
    
    try:
        # Decode base64 and parse JSON
        cursor_bytes = base64.b64decode(cursor.encode('utf-8'))
        cursor_data = cursor_bytes.decode('utf-8')
        return json.loads(cursor_data)
    except Exception as e:
        logger.warning("Failed to decode cursor", cursor=cursor, error=str(e))
        return None


def is_valid_cursor(cursor: Optional[str]) -> bool:
    """
    Validate if a cursor string is properly formatted and decodable.
    
    Args:
        cursor: Base64 encoded cursor string or None
        
    Returns:
        True if cursor is valid or None, False if invalid
    """
    if cursor is None:
        return True  # None is valid (no cursor)
    
    if not isinstance(cursor, str) or cursor == "":
        return False
    
    # Try to decode - if it fails, it's invalid
    return decode_cursor(cursor) is not None
