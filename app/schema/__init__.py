"""
DynamoDB schema definitions.
All database table schemas are defined here using PynamoDB.
"""

from .abend_dynamo import AbendDynamoTable
from .dynamo_config import DynamoDBConfig

__all__ = [
    "AbendDynamoTable",
    "DynamoDBConfig",
]
