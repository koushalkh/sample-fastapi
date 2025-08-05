"""
Table creation utility for DynamoDB tables.
This script can be used to create tables in local DynamoDB.
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from structlog import get_logger

from app.schema.abend_dynamo import AbendDynamoTable
from app.schema.sop_dynamo import SOPDynamoTable

logger = get_logger()


def create_abend_table() -> None:
    """Create the ABEND DynamoDB table if it doesn't exist."""
    try:
        if not AbendDynamoTable.exists():
            logger.info(
                "Creating ABEND table", table_name=AbendDynamoTable.Meta.table_name
            )
            AbendDynamoTable.create_table(
                read_capacity_units=1, write_capacity_units=1, wait=True
            )
            logger.info("ABEND table created successfully")
        else:
            logger.info(
                "ABEND table already exists",
                table_name=AbendDynamoTable.Meta.table_name,
            )
    except Exception as e:
        logger.error("Failed to create ABEND table", error=str(e))
        raise


def create_sop_table() -> None:
    """Create the SOP DynamoDB table if it doesn't exist."""
    try:
        if not SOPDynamoTable.exists():
            logger.info("Creating SOP table", table_name=SOPDynamoTable.Meta.table_name)
            SOPDynamoTable.create_table(
                read_capacity_units=1, write_capacity_units=1, wait=True
            )
            logger.info("SOP table created successfully")
        else:
            logger.info(
                "SOP table already exists",
                table_name=SOPDynamoTable.Meta.table_name,
            )
    except Exception as e:
        logger.error("Failed to create SOP table", error=str(e))
        raise


def create_all_tables() -> None:
    """Create all DynamoDB tables."""
    logger.info("Starting table creation process")
    create_abend_table()
    create_sop_table()
    logger.info("All tables created successfully")


if __name__ == "__main__":
    create_all_tables()
