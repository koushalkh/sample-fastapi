"""
ABEND Database Usage Examples

This file demonstrates how to use the AbendDynamoTable and related Pydantic models
for managing ABEND (Abnormal End) records in the system.
"""

from datetime import datetime, timezone
from typing import Dict, Any
import json

# Import the DynamoDB model
from app.schema.abend_dynamo import AbendDynamoTable

# Import Pydantic models for validation
from app.models.abend import (
    AbendModel, 
    AbendDetailsModel, 
    ADRStatusEnum, 
    SeverityEnum,
    EmailMetadata,
    KnowledgeBaseMetadata,
    KnowledgeBaseFile,
    RemediationMetadata
)


def example_1_create_basic_abend_record():
    """Example 1: Create a basic ABEND record with minimal required fields."""
    print("=== Example 1: Creating Basic ABEND Record ===")
    
    # Generate tracking ID
    job_name = "WGMP110D"
    tracking_id = AbendDynamoTable.generate_tracking_id(job_name)
    
    print(f"Generated Tracking ID: {tracking_id}")
    
    # Create the record
    abend_record = AbendDynamoTable(
        tracking_id=tracking_id,
        abended_at=datetime.now(timezone.utc),
        job_id="IYM98ID",
        job_name=job_name,
        adr_status=ADRStatusEnum.ABEND_REGISTERED.value,
        severity=SeverityEnum.HIGH.value,
        domain_area="Claims Processing",
        incident_number="INC03936788"
    )
    
    # Note: In real usage, you would call abend_record.save() to persist to DynamoDB
    print(f"Created ABEND record with status: {abend_record.adr_status}")
    print(f"Abended at: {abend_record.abended_at}")
    
    return abend_record


def example_2_create_detailed_abend_record():
    """Example 2: Create a detailed ABEND record with all fields."""
    print("\n=== Example 2: Creating Detailed ABEND Record ===")
    
    # Generate tracking ID
    tracking_id = AbendDynamoTable.generate_tracking_id("WGMP110D")
    
    # Create email metadata
    email_data = {
        "subject": "Batch Job X - Error 1050: Contention Detected",
        "from": "system@company.com",
        "to": "team@company.com",
        "sentDateTime": datetime.now(timezone.utc),
        "receivedDateTime": datetime.now(timezone.utc),
        "hasAttachments": False,
        "conversationID": "conv-1234567890",
        "messageID": "msg-0987654321"
    }
    
    # Create knowledge base metadata
    kb_data = {
        "relevantSOPId": "SOP-CONTENTION-001",
        "files": [
            {
                "fileName": "ADR_FAULT_example.TXT",
                "fileType": "application/txt",
                "fileSize": 204800,
                "fileUrl": "s3://adr_fault_files/adr_fault_1234.txt"
            }
        ]
    }
    
    # Create remediation metadata
    remediation_data = {
        "expandability": "AI suggests restarting job B because Job A ran at the same time with a locked database resource...",
        "confidenceScore": 0.92,
        "remediationRecommendations": "## Recommended Actions\n1. Restart Job B\n2. Check database locks\n3. Monitor for contention",
        "aiRemediationApprovalStatus": "Pending",
        "aiRemediationApprovalRequired": True,
        "aiRemediationComments": "High confidence remediation available"
    }
    
    # Create the detailed record
    abend_record = AbendDynamoTable(
        tracking_id=tracking_id,
        abended_at=datetime.now(timezone.utc),
        
        # Basic job information
        job_id="IYM98ID",
        job_name="WGMP110D",
        order_id="062525",
        incident_number="INC03936788",
        fa_id="F72550",
        domain_area="Claims Processing",
        
        # ABEND specific information
        abend_type="EFX",
        abend_step="02",
        abend_return_code="10",
        abend_reason="Error 1050: Contention",
        
        # Status and severity
        adr_status=ADRStatusEnum.LOG_EXTRACTION_INITIATED.value,
        severity=SeverityEnum.HIGH.value,
        
        # Performance metrics (flattened)
        perf_log_extraction_time="180s",
        perf_ai_analysis_time="240s",
        perf_remediation_time="120s",
        perf_total_automated_time="540s",
        
        # Log extraction metadata (flattened)
        log_extraction_run_id="3238576549654",
        log_extraction_retries=0,
        
        # Audit fields
        created_by="system",
        updated_by="system",
        generation=1
    )
    
    # Set complex nested objects using helper methods
    abend_record.set_email_metadata(email_data)
    abend_record.set_knowledge_base_metadata(kb_data)
    abend_record.set_remediation_metadata(remediation_data)
    
    print(f"Created detailed ABEND record: {tracking_id}")
    print(f"Status: {abend_record.adr_status}")
    print(f"Email subject: {abend_record.email_metadata['subject']}")
    
    return abend_record


def example_3_query_by_status():
    """Example 3: Query ABEND records by ADR status."""
    print("\n=== Example 3: Querying by ADR Status ===")
    
    # Example of how you would query using the ADRStatusIndex
    # Note: This is pseudo-code for demonstration
    
    status_to_query = ADRStatusEnum.LOG_EXTRACTION_INITIATED.value
    today = datetime.now(timezone.utc)
    today_iso = AbendDynamoTable.datetime_to_iso_string(today)
    
    print(f"Query pattern for status '{status_to_query}':")
    print(f"  - Hash key: {status_to_query}")
    print(f"  - Range key starts with: {today_iso[:10]} (for today's records)")
    print(f"  - Use: AbendDynamoTable.adr_status_index.query()")
    
    # Real query would look like:
    # results = AbendDynamoTable.adr_status_index.query(
    #     hash_key=status_to_query,
    #     range_key_condition=AbendDynamoTable.abended_at.startswith(today_iso[:10])
    # )


def example_4_query_by_severity():
    """Example 4: Query ABEND records by severity."""
    print("\n=== Example 4: Querying by Severity ===")
    
    severity_to_query = SeverityEnum.HIGH.value
    today = datetime.now(timezone.utc)
    today_iso = AbendDynamoTable.datetime_to_iso_string(today)
    
    print(f"Query pattern for severity '{severity_to_query}':")
    print(f"  - Hash key: {severity_to_query}")
    print(f"  - Range key starts with: {today_iso[:10]} (for today's records)")
    print(f"  - Use: AbendDynamoTable.severity_index.query()")


def example_5_update_abend_status():
    """Example 5: Update ABEND record status as it progresses through the workflow."""
    print("\n=== Example 5: Updating ABEND Status ===")
    
    # Simulate status progression
    status_progression = [
        ADRStatusEnum.ABEND_REGISTERED,
        ADRStatusEnum.LOG_EXTRACTION_INITIATED,
        ADRStatusEnum.LOG_UPLOAD_TO_S3,
        ADRStatusEnum.PREPROCESSING_LOG_FILE,
        ADRStatusEnum.AI_ANALYSIS_INITIATED,
        ADRStatusEnum.REMEDIATION_SUGGESTIONS_GENERATED,
        ADRStatusEnum.PENDING_MANUAL_APPROVAL,
        ADRStatusEnum.VERIFICATION_IN_PROGRESS,
        ADRStatusEnum.RESOLVED
    ]
    
    print("Status progression workflow:")
    for i, status in enumerate(status_progression, 1):
        print(f"  {i}. {status.value}")
    
    # Example of updating a record
    print("\nExample update process:")
    print("1. Retrieve record by tracking_id")
    print("2. Update adr_status field")
    print("3. Update any relevant metadata")
    print("4. Call save() method (auto-updates updated_at and generation)")


def example_6_pydantic_validation():
    """Example 6: Using Pydantic models for API validation."""
    print("\n=== Example 6: Pydantic Model Validation ===")
    
    # Example API payload
    api_payload = {
        "trackingID": "ABEND_WGMP110D_01ARZ3NDEKTSV4RRFFQ69G5FAV",
        "jobID": "IYM98ID",
        "jobName": "WGMP110D",
        "abendedAt": "2024-01-15T10:30:00Z",
        "adrStatus": "ABEND_REGISTERED",
        "severity": "High",
        "domainArea": "Claims Processing",
        "incidentNumber": "INC03936788",
        "createdAt": "2024-01-15T10:30:00Z",
        "updatedAt": "2024-01-15T10:30:00Z"
    }
    
    try:
        # Validate with basic model (for table display)
        basic_model = AbendModel(**api_payload)
        print("✅ Basic model validation passed")
        print(f"   Tracking ID: {basic_model.tracking_id}")
        print(f"   Status: {basic_model.adr_status}")
        
        # For detailed views, use AbendDetailsModel
        detailed_payload = {
            **api_payload,
            "orderID": "062525",
            "faID": "F72550",
            "abendType": "EFX",
            "abendStep": "02",
            "perfLogExtractionTime": "180s",
            "logExtractionRunId": "3238576549654",
            "logExtractionRetries": 0,
            "createdBy": "system",
            "updatedBy": "system",
            "generation": 1
        }
        
        detailed_model = AbendDetailsModel(**detailed_payload)
        print("✅ Detailed model validation passed")
        print(f"   FA ID: {detailed_model.fa_id}")
        print(f"   Generation: {detailed_model.generation}")
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")


def example_7_datetime_handling():
    """Example 7: Proper datetime handling for GSI queries."""
    print("\n=== Example 7: Datetime Handling ===")
    
    # Current datetime
    now = datetime.now(timezone.utc)
    print(f"Current UTC datetime: {now}")
    
    # Convert to ISO string for GSI queries
    iso_string = AbendDynamoTable.datetime_to_iso_string(now)
    print(f"ISO string for GSI: {iso_string}")
    
    # Convert back to datetime
    converted_back = AbendDynamoTable.iso_string_to_datetime(iso_string)
    print(f"Converted back: {converted_back}")
    
    # Example: Query for records from the last hour
    one_hour_ago = now.replace(minute=now.minute-60) if now.minute >= 60 else now.replace(hour=now.hour-1, minute=0)
    one_hour_ago_iso = AbendDynamoTable.datetime_to_iso_string(one_hour_ago)
    
    print(f"\nFor querying records from last hour:")
    print(f"  Start time (ISO): {one_hour_ago_iso}")
    print(f"  End time (ISO): {iso_string}")


if __name__ == "__main__":
    """Run all examples to demonstrate ABEND database usage."""
    print("🚀 ABEND Database Usage Examples\n")
    
    # Run all examples
    example_1_create_basic_abend_record()
    example_2_create_detailed_abend_record()
    example_3_query_by_status()
    example_4_query_by_severity()
    example_5_update_abend_status()
    example_6_pydantic_validation()
    example_7_datetime_handling()
    
    print("\n✅ All examples completed!")
    print("\nNote: These examples demonstrate the structure and usage patterns.")
    print("In a real application, you would:")
    print("1. Configure DynamoDB connection properly")
    print("2. Handle exceptions and error cases")
    print("3. Add proper logging and monitoring")
    print("4. Implement retry logic for database operations")
