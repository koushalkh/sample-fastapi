"""
Data Access Layer for SOP operations.

This module provides optimized database access functions for SOP records
using strategic DynamoDB query patterns and GSI design.

ACCESS PATTERNS & OPTIMIZATIONS:
1. Get by sopId (Primary Key): Direct PK query - 1 RCU
2. List by job_name: JobNameIndex query - 2-5 RCU
3. List by abend_type: AbendTypeIndex query - 2-5 RCU
4. List with filters: GSI query + filter expressions - 3-8 RCU

FILTER STRATEGY:
- All filtering done via DynamoDB filter expressions
- GSI queries with date-based sorting
- Cursor-based pagination for optimal performance

CAPACITY PLANNING:
- Expected lower volume than ABEND records
- GSI capacity set to 2 RCU/WCU initially
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from structlog import get_logger

from app.models.sop import SOPDetailsModel, SOPModel
from app.schema.sop_dynamo import SOPDynamoTable

logger = get_logger(__name__)


def get_sop_by_id(sop_id: str) -> Optional[SOPDetailsModel]:
    """
    Get SOP record by ID using primary key query (most efficient).

    Args:
        sop_id: The SOP ID to retrieve

    Returns:
        SOPDetailsModel if found, None otherwise

    Raises:
        Exception if query fails
    """
    try:
        logger.info("Getting SOP by ID", sop_id=sop_id)

        # Direct primary key query - most efficient
        sop_record = SOPDynamoTable.get(sop_id, "SOP")

        if not sop_record:
            logger.info("SOP not found", sop_id=sop_id)
            return None

        logger.info("SOP retrieved successfully", sop_id=sop_id)
        return _convert_to_sop_details_model(sop_record)

    except SOPDynamoTable.DoesNotExist:
        logger.info("SOP does not exist", sop_id=sop_id)
        return None
    except Exception as e:
        logger.error("Error getting SOP by ID", sop_id=sop_id, error=str(e))
        raise


def get_sops_by_job_name(
    job_name: str, limit: int = 50, last_evaluated_key: Optional[Dict[str, Any]] = None
) -> Tuple[List[SOPModel], Optional[Dict[str, Any]]]:
    """
    Get SOPs for a specific job name using JobNameIndex.

    Args:
        job_name: Job name to filter by
        limit: Maximum number of records to return
        last_evaluated_key: Pagination key from previous query

    Returns:
        Tuple of (SOP records, next page key)

    Raises:
        Exception if query fails
    """
    try:
        logger.info("Getting SOPs by job name", job_name=job_name, limit=limit)

        # Query using JobNameIndex GSI
        query_kwargs = {
            "hash_key": job_name,
            "limit": limit,
            "scan_index_forward": False,  # Most recent first
        }

        if last_evaluated_key:
            query_kwargs["last_evaluated_key"] = last_evaluated_key

        results = SOPDynamoTable.job_name_index.query(**query_kwargs)

        # Convert to list and extract pagination info
        records = []
        next_page_key = None

        for record in results:
            records.append(_convert_to_sop_model(record))

        # Get pagination key if there are more results
        if hasattr(results, "last_evaluated_key") and results.last_evaluated_key:
            next_page_key = results.last_evaluated_key

        logger.info(
            "SOPs retrieved by job name",
            job_name=job_name,
            count=len(records),
            has_next=next_page_key is not None,
        )

        return records, next_page_key

    except Exception as e:
        logger.error("Error getting SOPs by job name", job_name=job_name, error=str(e))
        raise


def get_sops_by_abend_type(
    abend_type: str,
    limit: int = 50,
    last_evaluated_key: Optional[Dict[str, Any]] = None,
) -> Tuple[List[SOPModel], Optional[Dict[str, Any]]]:
    """
    Get SOPs for a specific abend type using AbendTypeIndex.

    Args:
        abend_type: Abend type to filter by
        limit: Maximum number of records to return
        last_evaluated_key: Pagination key from previous query

    Returns:
        Tuple of (SOP records, next page key)

    Raises:
        Exception if query fails
    """
    try:
        logger.info("Getting SOPs by abend type", abend_type=abend_type, limit=limit)

        # Query using AbendTypeIndex GSI
        query_kwargs = {
            "hash_key": abend_type,
            "limit": limit,
            "scan_index_forward": False,  # Most recent first
        }

        if last_evaluated_key:
            query_kwargs["last_evaluated_key"] = last_evaluated_key

        results = SOPDynamoTable.abend_type_index.query(**query_kwargs)

        # Convert to list and extract pagination info
        records = []
        next_page_key = None

        for record in results:
            records.append(_convert_to_sop_model(record))

        # Get pagination key if there are more results
        if hasattr(results, "last_evaluated_key") and results.last_evaluated_key:
            next_page_key = results.last_evaluated_key

        logger.info(
            "SOPs retrieved by abend type",
            abend_type=abend_type,
            count=len(records),
            has_next=next_page_key is not None,
        )

        return records, next_page_key

    except Exception as e:
        logger.error(
            "Error getting SOPs by abend type", abend_type=abend_type, error=str(e)
        )
        raise


def get_sops_unified(
    job_name: Optional[str] = None,
    abend_type: Optional[str] = None,
    search_term: Optional[str] = None,
    limit: int = 50,
    last_evaluated_key: Optional[Dict[str, Any]] = None,
) -> Tuple[List[SOPModel], Optional[Dict[str, Any]]]:
    """
    Unified function to get SOPs with various filters.

    Args:
        job_name: Filter by job name (uses JobNameIndex)
        abend_type: Filter by abend type (uses AbendTypeIndex)
        search_term: Search in SOP name (applied as filter)
        limit: Maximum number of records to return
        last_evaluated_key: Pagination key from previous query

    Returns:
        Tuple of (SOP records, next page key)

    Raises:
        Exception if query fails
    """
    try:
        logger.info(
            "Getting SOPs with unified query",
            job_name=job_name,
            abend_type=abend_type,
            search_term=search_term,
            limit=limit,
        )

        # Determine query strategy based on available filters
        if job_name:
            # Use JobNameIndex
            records, next_key = get_sops_by_job_name(
                job_name, limit, last_evaluated_key
            )
        elif abend_type:
            # Use AbendTypeIndex
            records, next_key = get_sops_by_abend_type(
                abend_type, limit, last_evaluated_key
            )
        else:
            # Scan table (less efficient, but needed for search-only queries)
            logger.warning(
                "Performing table scan for SOP query - consider adding filters"
            )
            records, next_key = _scan_sops_with_filters(
                search_term, limit, last_evaluated_key
            )

        # Apply search filter if provided (post-query filtering)
        if search_term and search_term.strip():
            search_lower = search_term.lower().strip()
            filtered_records = [
                record for record in records if search_lower in record.sop_name.lower()
            ]
            records = filtered_records

        logger.info(
            "Unified SOP query completed",
            count=len(records),
            has_next=next_key is not None,
        )

        return records, next_key

    except Exception as e:
        logger.error("Error in unified SOP query", error=str(e))
        raise


def create_sop(
    sop_name: str,
    job_name: str,
    abend_type: str,
    source_document_url: str,
    processed_document_urls: Optional[List[str]] = None,
    created_by: str = "system",
) -> SOPDetailsModel:
    """
    Create a new SOP record.

    Args:
        sop_name: Name of the SOP
        job_name: Associated job name
        abend_type: Type of abend this SOP addresses
        source_document_url: S3 URL of original document
        processed_document_urls: List of S3 URLs for processed documents
        created_by: Who is creating this SOP

    Returns:
        SOPDetailsModel of created record

    Raises:
        Exception if creation fails
    """
    sop_id = SOPDynamoTable.generate_sop_id()

    logger.info(
        "Creating new SOP record",
        sop_id=sop_id,
        sop_name=sop_name,
        job_name=job_name,
        abend_type=abend_type,
    )

    try:
        # Generate current timestamp
        now = datetime.now(timezone.utc)

        # Create new SOP record
        sop_record = SOPDynamoTable(
            # Primary key
            sop_id=sop_id,
            record_type="SOP",
            # Basic information
            sop_name=sop_name,
            job_name=job_name,
            abend_type=abend_type,
            # Document URLs
            source_document_url=source_document_url,
            processed_document_urls=processed_document_urls or [],
            # Audit fields
            created_at=now,
            updated_at=now,
            created_by=created_by,
            updated_by=created_by,
            generation=1,
        )

        # Save to DynamoDB
        sop_record.save()

        logger.info(
            "Successfully created SOP record",
            sop_id=sop_id,
            sop_name=sop_name,
            job_name=job_name,
        )

        # Convert to model and return
        return _convert_to_sop_details_model(sop_record)

    except Exception as e:
        logger.error(
            "Error creating SOP record", sop_id=sop_id, sop_name=sop_name, error=str(e)
        )
        raise


def update_sop_fields(sop_id: str, updates: Dict[str, Any]) -> bool:
    """
    Update specific fields of a SOP record.

    Args:
        sop_id: The SOP ID to update
        updates: Dictionary of field updates

    Returns:
        True if update successful, False if record not found

    Raises:
        Exception if update fails
    """
    try:
        logger.info("Updating SOP fields", sop_id=sop_id, fields=list(updates.keys()))

        # Get existing record
        sop_record = SOPDynamoTable.get(sop_id, "SOP")

        # Apply updates
        for field, value in updates.items():
            if hasattr(sop_record, field):
                setattr(sop_record, field, value)

        # Always update the timestamp and generation
        sop_record.updated_at = datetime.now(timezone.utc)
        sop_record.generation += 1

        # Save changes
        sop_record.save()

        logger.info("SOP fields updated successfully", sop_id=sop_id)
        return True

    except SOPDynamoTable.DoesNotExist:
        logger.warning("SOP not found for update", sop_id=sop_id)
        return False
    except Exception as e:
        logger.error("Error updating SOP fields", sop_id=sop_id, error=str(e))
        raise


def _scan_sops_with_filters(
    search_term: Optional[str] = None,
    limit: int = 50,
    last_evaluated_key: Optional[Dict[str, Any]] = None,
) -> Tuple[List[SOPModel], Optional[Dict[str, Any]]]:
    """
    Scan SOPs table with filters (less efficient, used when no GSI matches).

    Args:
        search_term: Search term for SOP name
        limit: Maximum records to return
        last_evaluated_key: Pagination key

    Returns:
        Tuple of (SOP records, next page key)
    """
    try:
        scan_kwargs = {"limit": limit}

        if last_evaluated_key:
            scan_kwargs["last_evaluated_key"] = last_evaluated_key

        # Add filter for record type
        filter_condition = SOPDynamoTable.record_type == "SOP"

        if search_term and search_term.strip():
            # Add search filter (DynamoDB contains operation)
            search_filter = SOPDynamoTable.sop_name.contains(search_term.strip())
            filter_condition = filter_condition & search_filter

        scan_kwargs["filter_condition"] = filter_condition

        results = SOPDynamoTable.scan(**scan_kwargs)

        # Convert results
        records = []
        next_page_key = None

        for record in results:
            records.append(_convert_to_sop_model(record))

        if hasattr(results, "last_evaluated_key") and results.last_evaluated_key:
            next_page_key = results.last_evaluated_key

        return records, next_page_key

    except Exception as e:
        logger.error("Error scanning SOPs", error=str(e))
        raise


# Conversion helpers
def _convert_to_sop_model(record: SOPDynamoTable) -> SOPModel:
    """Convert DynamoDB record to SOPModel."""
    # Convert datetime strings back to datetime objects if needed
    created_at = record.created_at
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))

    updated_at = record.updated_at
    if isinstance(updated_at, str):
        updated_at = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))

    return SOPModel(
        sopID=record.sop_id,
        sopName=record.sop_name,
        jobName=record.job_name,
        abendType=record.abend_type,
        createdAt=created_at,
        updatedAt=updated_at,
        createdBy=record.created_by,
    )


def _convert_to_sop_details_model(record: SOPDynamoTable) -> SOPDetailsModel:
    """Convert DynamoDB record to SOPDetailsModel."""
    # Convert datetime strings back to datetime objects if needed
    created_at = record.created_at
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))

    updated_at = record.updated_at
    if isinstance(updated_at, str):
        updated_at = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))

    return SOPDetailsModel(
        # Basic fields
        sopID=record.sop_id,
        sopName=record.sop_name,
        jobName=record.job_name,
        abendType=record.abend_type,
        # Document URLs
        sourceDocumentUrl=record.source_document_url,
        processedDocumentUrls=(
            list(record.processed_document_urls)
            if record.processed_document_urls
            else []
        ),
        # Audit fields
        createdAt=created_at,
        updatedAt=updated_at,
        createdBy=record.created_by,
        updatedBy=record.updated_by,
        generation=record.generation,
    )
