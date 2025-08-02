"""
Database Access Layer for ABEND operations.

This module contains pure functions for database operations related to ABENDs.
All business logic should be in the core layer, this layer only handles data access.
Uses GSI optimization for efficient querying at scale.
"""

from datetime import date, datetime, timezone
from typing import List, Optional, Dict, Tuple, Any, Union
from structlog import get_logger

from app.schema.abend_dynamo import AbendDynamoTable
from app.models.abend import (
    AbendModel, 
    AbendDetailsModel, 
    ADRStatusEnum, 
    SeverityEnum,
    AIRemediationApprovalStatusEnum
)

logger = get_logger(__name__)


def get_abends_with_filters(
    domain_area: Optional[str] = None,
    adr_status: Optional[ADRStatusEnum] = None,
    severity: Optional[SeverityEnum] = None,
    abended_at: Optional[date] = None,
    abended_at_start_date: Optional[date] = None,
    abended_at_end_date: Optional[date] = None,
    search: Optional[str] = None,
    limit: int = 5,
    offset: int = 0
) -> Tuple[List[AbendModel], int]:
    """
    Get ABEND records with filters and pagination using optimized GSI queries.
    
    Args:
        domain_area: Filter by domain area
        adr_status: Filter by ADR status
        severity: Filter by severity level
        abended_at: Filter by specific date
        abended_at_start_date: Start date for range filter
        abended_at_end_date: End date for range filter
        search: Search by job name
        limit: Number of records per page
        offset: Number of records to skip
        
    Returns:
        Tuple of (records, total_count)
    """
    try:
        logger.info("Getting ABENDs with filters using GSI optimization", 
                   domain_area=domain_area, adr_status=adr_status, severity=severity,
                   abended_at=abended_at, search=search, limit=limit, offset=offset)
        
        # Use GSI queries for optimal performance
        records = _get_records_with_gsi_optimization(
            domain_area=domain_area,
            adr_status=adr_status,
            severity=severity,
            search=search,
            abended_at=abended_at,
            abended_at_start_date=abended_at_start_date,
            abended_at_end_date=abended_at_end_date
        )
        
        # Sort by abended_at (default sort order)
        sorted_records = sorted(records, key=lambda x: x.abended_at, reverse=True)
        
        # Apply pagination
        total_count = len(sorted_records)
        paginated_records = sorted_records[offset:offset + limit]
        
        # Convert to response models
        abend_models = [_convert_to_abend_model(record) for record in paginated_records]
        
        logger.info("Successfully retrieved ABENDs", 
                   returned_count=len(abend_models), total_count=total_count)
        
        return abend_models, total_count
        
    except Exception as e:
        logger.error("Error getting ABENDs with filters", error=str(e))
        raise


def get_abend_by_tracking_id(tracking_id: str) -> Optional[AbendDetailsModel]:
    """
    Get ABEND details by tracking ID.
    Since tracking_id is the hash key but we need both keys for GetItem,
    we'll use a query with only hash key to find the record.
    
    Args:
        tracking_id: ABEND tracking ID
        
    Returns:
        AbendDetailsModel or None if not found
    """
    try:
        logger.info("Getting ABEND by tracking ID", tracking_id=tracking_id)
        
        # Query by tracking_id (hash key only)
        records = list(AbendDynamoTable.query(tracking_id))
        
        if records:
            # Should only be one record per tracking_id
            record = records[0]
            abend_details = _convert_to_abend_details_model(record)
            logger.info("Successfully retrieved ABEND details", tracking_id=tracking_id)
            return abend_details
        else:
            logger.info("ABEND not found", tracking_id=tracking_id)
            return None
            
    except Exception as e:
        if "DoesNotExist" in str(type(e)):
            logger.info("ABEND not found", tracking_id=tracking_id)
            return None
        logger.error("Error getting ABEND by tracking ID", tracking_id=tracking_id, error=str(e))
        raise


def update_abend_fields(
    tracking_id: str,
    field_updates: Dict[str, Any],
    updated_by: str = "system"
) -> bool:
    """
    Generic update method that can update any subset of fields, including nested ones.
    
    Args:
        tracking_id: ABEND tracking ID
        field_updates: Dictionary of field names and their new values
        updated_by: User who made the update
        
    Returns:
        True if successful, False if record not found
        
    Examples:
        # Update simple fields
        update_abend_fields("ABEND_123", {"severity": "High", "adr_status": "RESOLVED"})
        
        # Update nested remediation metadata
        update_abend_fields("ABEND_123", {
            "remediation_metadata": {
                "aiRemediationApprovalStatus": "APPROVED",
                "aiRemediationComments": "Looks good"
            }
        })
        
        # Update performance metrics
        update_abend_fields("ABEND_123", {
            "perf_log_extraction_time": "120s",
            "perf_ai_analysis_time": "45s"
        })
    """
    try:
        logger.info("Updating ABEND fields", tracking_id=tracking_id, fields=list(field_updates.keys()))
        
        # Get the record using query (since we need both keys for get)
        records = list(AbendDynamoTable.query(tracking_id))
        
        if not records:
            logger.error("ABEND not found for update", tracking_id=tracking_id)
            return False
            
        record = records[0]  # Should only be one record per tracking_id
        
        # Apply updates
        for field_name, field_value in field_updates.items():
            if field_name in ["email_metadata", "emailMetadata"]:
                record.set_email_metadata(field_value)
            elif field_name in ["knowledge_base_metadata", "knowledgeBaseMetadata"]:
                record.set_knowledge_base_metadata(field_value)
            elif field_name in ["remediation_metadata", "remediationMetadata"]:
                # For nested updates, merge with existing data
                if isinstance(field_value, dict):
                    current_metadata = record.get_remediation_metadata() or {}
                    current_metadata.update(field_value)
                    record.set_remediation_metadata(current_metadata)
                else:
                    record.set_remediation_metadata(field_value)
            else:
                # Handle regular field updates
                if hasattr(record, field_name):
                    setattr(record, field_name, field_value)
                else:
                    logger.warning("Unknown field in update", field=field_name, tracking_id=tracking_id)
        
        # Update audit fields
        record.updated_by = updated_by
        record.updated_at = datetime.now(timezone.utc)
        
        # Save the record
        record.save()
        
        logger.info("Successfully updated ABEND fields", tracking_id=tracking_id)
        return True
        
    except Exception as e:
        if "DoesNotExist" in str(type(e)):
            logger.error("ABEND not found for update", tracking_id=tracking_id)
            return False
        logger.error("Error updating ABEND fields", tracking_id=tracking_id, error=str(e))
        raise


def update_remediation_approval(
    tracking_id: str,
    approval_status: AIRemediationApprovalStatusEnum,
    comments: Optional[str] = None,
    approved_by: str = "system"
) -> bool:
    """
    Update AI remediation approval status for an ABEND.
    
    Args:
        tracking_id: ABEND tracking ID
        approval_status: Approval status (APPROVED/REJECTED)
        comments: Approval comments
        approved_by: User who approved
        
    Returns:
        True if successful, False otherwise
    """
    remediation_updates = {
        'aiRemediationApprovalStatus': approval_status.value,
        'aiRemediationComments': comments,
        'aiRemediationApprovedAt': datetime.now(timezone.utc).isoformat()
    }
    
    return update_abend_fields(
        tracking_id=tracking_id,
        field_updates={"remediation_metadata": remediation_updates},
        updated_by=approved_by
    )


def get_available_filter_values() -> Dict[str, List[str]]:
    """
    Get available filter values for domain areas, ADR statuses, and severities.
    Uses optimized scanning with projection to minimize data transfer.
    
    Returns:
        Dictionary with lists of available values
    """
    try:
        logger.info("Getting available filter values with optimized scan")
        
        # Use scan with projection to only get the fields we need
        all_records = list(AbendDynamoTable.scan(
            attributes_to_get=['domain_area', 'adr_status', 'severity']
        ))
        
        # Extract unique values
        domain_areas: set[str] = set()
        adr_statuses: set[str] = set()
        severities: set[str] = set()
        
        for record in all_records:
            if hasattr(record, 'domain_area') and record.domain_area:
                domain_areas.add(record.domain_area)
            if hasattr(record, 'adr_status') and record.adr_status:
                adr_statuses.add(record.adr_status)
            if hasattr(record, 'severity') and record.severity:
                severities.add(record.severity)
        
        result = {
            'domain_areas': sorted(list(domain_areas)),
            'adr_statuses': sorted(list(adr_statuses)),
            'severities': sorted(list(severities))
        }
        
        logger.info("Successfully retrieved filter values", 
                   domain_areas_count=len(result['domain_areas']),
                   adr_statuses_count=len(result['adr_statuses']),
                   severities_count=len(result['severities']))
        
        return result
        
    except Exception as e:
        logger.error("Error getting available filter values", error=str(e))
        raise


def get_today_stats(target_date: Optional[date] = None) -> Dict[str, int]:
    """
    Get today's ABEND statistics using optimized GSI queries.
    
    Args:
        target_date: Date to get stats for (defaults to today)
        
    Returns:
        Dictionary with statistics
    """
    try:
        if not target_date:
            target_date = date.today()
            
        logger.info("Getting today's stats with GSI optimization", target_date=target_date)
        
        # Use GSI queries for better performance when possible
        date_str = target_date.isoformat()
        
        # Get counts using different strategies
        total_abends = _count_abends_for_date(target_date)
        resolved_abends = _count_abends_by_status_and_date(ADRStatusEnum.RESOLVED, target_date)
        manual_intervention_required = _count_abends_by_status_and_date(
            ADRStatusEnum.MANUAL_INTERVENTION_REQUIRED, target_date
        )
        
        active_abends = total_abends - resolved_abends
        
        stats = {
            'total_abends': total_abends,
            'active_abends': active_abends,
            'manual_intervention_required': manual_intervention_required,
            'resolved_abends': resolved_abends
        }
        
        logger.info("Successfully retrieved today's stats", **stats)
        
        return stats
        
    except Exception as e:
        logger.error("Error getting today's stats", target_date=target_date, error=str(e))
        raise


# Private helper functions for GSI optimization

def _get_records_with_gsi_optimization(
    domain_area: Optional[str] = None,
    adr_status: Optional[ADRStatusEnum] = None,
    severity: Optional[SeverityEnum] = None,
    search: Optional[str] = None,
    abended_at: Optional[date] = None,
    abended_at_start_date: Optional[date] = None,
    abended_at_end_date: Optional[date] = None
) -> List[Any]:
    """
    Get records using the most efficient GSI query based on available filters.
    
    Priority order:
    1. If adr_status provided -> use ADRStatusIndex
    2. If severity provided -> use SeverityIndex  
    3. If domain_area provided -> use DomainAreaIndex
    4. If search (job_name) provided -> use JobNameIndex
    5. Otherwise -> fall back to scan with filters
    """
    
    records = []
    
    if adr_status:
        logger.info("Using ADRStatusIndex for optimized query", adr_status=adr_status.value)
        records = list(AbendDynamoTable.adr_status_index.query(hash_key=adr_status.value))
        
    elif severity:
        logger.info("Using SeverityIndex for optimized query", severity=severity.value)
        records = list(AbendDynamoTable.severity_index.query(hash_key=severity.value))
        
    elif domain_area:
        logger.info("Using DomainAreaIndex for optimized query", domain_area=domain_area)
        records = list(AbendDynamoTable.domain_area_index.query(hash_key=domain_area))
        
    elif search:
        logger.info("Using JobNameIndex for optimized query", job_name=search)
        records = list(AbendDynamoTable.job_name_index.query(hash_key=search))
        
    else:
        logger.info("Using scan as no specific GSI filter provided")
        records = list(AbendDynamoTable.scan())
    
    # Apply remaining filters
    filtered_records = _apply_remaining_filters(
        records,
        domain_area=domain_area if not domain_area or len(records) == 0 else None,
        adr_status=adr_status if not adr_status or len(records) == 0 else None,
        severity=severity if not severity or len(records) == 0 else None,
        search=search if not search or len(records) == 0 else None,
        abended_at=abended_at,
        abended_at_start_date=abended_at_start_date,
        abended_at_end_date=abended_at_end_date
    )
    
    return filtered_records


def _count_abends_for_date(target_date: date) -> int:
    """Count total ABENDs for a specific date using optimized scan."""
    try:
        count = 0
        for record in AbendDynamoTable.scan(attributes_to_get=['abended_at']):
            if hasattr(record, 'abended_at') and record.abended_at.date() == target_date:
                count += 1
        return count
    except Exception:
        return 0


def _count_abends_by_status_and_date(status: ADRStatusEnum, target_date: date) -> int:
    """Count ABENDs by status for a specific date using GSI."""
    try:
        count = 0
        for record in AbendDynamoTable.adr_status_index.query(hash_key=status.value):
            if hasattr(record, 'abended_at') and record.abended_at.date() == target_date:
                count += 1
        return count
    except Exception:
        return 0


def _apply_remaining_filters(
    records: List[Any],
    domain_area: Optional[str] = None,
    adr_status: Optional[ADRStatusEnum] = None,
    severity: Optional[SeverityEnum] = None,
    search: Optional[str] = None,
    abended_at: Optional[date] = None,
    abended_at_start_date: Optional[date] = None,
    abended_at_end_date: Optional[date] = None
) -> List[Any]:
    """Apply remaining filters that weren't used in the initial GSI query."""
    
    filtered = records
    
    # Apply remaining filters
    if domain_area:
        filtered = [r for r in filtered if hasattr(r, 'domain_area') and r.domain_area == domain_area]
    
    if adr_status:
        filtered = [r for r in filtered if hasattr(r, 'adr_status') and r.adr_status == adr_status.value]
    
    if severity:
        filtered = [r for r in filtered if hasattr(r, 'severity') and r.severity == severity.value]
    
    if search:
        search_lower = search.lower()
        filtered = [
            r for r in filtered 
            if hasattr(r, 'job_name') and search_lower in r.job_name.lower()
        ]
    
    # Date filters
    if abended_at:
        filtered = [r for r in filtered if hasattr(r, 'abended_at') and r.abended_at.date() == abended_at]
    elif abended_at_start_date and abended_at_end_date:
        filtered = [
            r for r in filtered 
            if hasattr(r, 'abended_at') and abended_at_start_date <= r.abended_at.date() <= abended_at_end_date
        ]
    elif abended_at_start_date:
        filtered = [r for r in filtered if hasattr(r, 'abended_at') and r.abended_at.date() >= abended_at_start_date]
    elif abended_at_end_date:
        filtered = [r for r in filtered if hasattr(r, 'abended_at') and r.abended_at.date() <= abended_at_end_date]
    
    return filtered


def _convert_to_abend_model(record: Any) -> AbendModel:
    """Convert DynamoDB record to AbendModel."""
    return AbendModel(
        trackingID=record.tracking_id,
        jobID=record.job_id,
        jobName=record.job_name,
        adrStatus=ADRStatusEnum(record.adr_status),
        severity=SeverityEnum(record.severity),
        abendedAt=record.abended_at,
        domainArea=record.domain_area,
        createdAt=record.created_at,
        updatedAt=record.updated_at
    )


def _convert_to_abend_details_model(record: Any) -> AbendDetailsModel:
    """Convert DynamoDB record to AbendDetailsModel."""
    return AbendDetailsModel(
        trackingID=record.tracking_id,
        jobID=record.job_id,
        jobName=record.job_name,
        abendedAt=record.abended_at,
        adrStatus=ADRStatusEnum(record.adr_status),
        severity=SeverityEnum(record.severity),
        domainArea=record.domain_area,
        incidentNumber=record.incident_number,
        orderID=record.order_id,
        faID=record.fa_id,
        abendStep=record.abend_step,
        abendReturnCode=record.abend_return_code,
        abendReason=record.abend_reason,
        abendType=record.abend_type,
        perfLogExtractionTime=record.perf_log_extraction_time,
        perfAiAnalysisTime=record.perf_ai_analysis_time,
        perfRemediationTime=record.perf_remediation_time,
        perfTotalAutomatedTime=record.perf_total_automated_time,
        logExtractionRunId=record.log_extraction_run_id,
        logExtractionRetries=record.log_extraction_retries,
        emailMetadata=record.get_email_metadata(),
        knowledgeBaseMetadata=record.get_knowledge_base_metadata(),
        remediationMetadata=record.get_remediation_metadata(),
        createdAt=record.created_at,
        updatedAt=record.updated_at,
        createdBy=record.created_by,
        updatedBy=record.updated_by,
        generation=record.generation
    )
