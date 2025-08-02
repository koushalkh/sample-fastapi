"""
ABEND Schema Examples

This file demonstrates the structure and usage patterns for ABEND models.
"""

from datetime import datetime, timezone

# Example JSON payloads for different use cases
def get_basic_abend_payload():
    """Basic ABEND payload for table display."""
    return {
        "trackingID": "ABEND_WGMP110D_01ARZ3NDEKTSV4RRFFQ69G5FAV",
        "jobID": "IYM98ID", 
        "jobName": "WGMP110D",
        "abendedAt": datetime.now(timezone.utc),
        "adrStatus": "ABEND_REGISTERED",
        "severity": "High",
        "domainArea": "Claims Processing",
        "incidentNumber": "INC03936788",
        "createdAt": datetime.now(timezone.utc),
        "updatedAt": datetime.now(timezone.utc)
    }


def get_detailed_abend_payload():
    """Complete ABEND payload with all fields."""
    return {
        # Basic fields
        "trackingID": "ABEND_WGMP110D_01ARZ3NDEKTSV4RRFFQ69G5FAV",
        "jobID": "IYM98ID",
        "jobName": "WGMP110D", 
        "abendedAt": datetime.now(timezone.utc),
        "adrStatus": "REMEDIATION_SUGGESTIONS_GENERATED",
        "severity": "High",
        "domainArea": "Claims Processing",
        "incidentNumber": "INC03936788",
        
        # Additional basic fields
        "orderID": "062525",
        "faID": "F72550",
        "abendStep": "02",
        "abendReturnCode": "10",
        "abendReason": "Error 1050: Contention",
        "abendType": "EFX",
        
        # Performance metrics (flattened)
        "perfLogExtractionTime": "180s",
        "perfAiAnalysisTime": "240s", 
        "perfRemediationTime": "120s",
        "perfTotalAutomatedTime": "540s",
        
        # Log extraction metadata (flattened)
        "logExtractionRunId": "3238576549654",
        "logExtractionRetries": 0,
        
        # Complex nested objects
        "emailMetadata": {
            "subject": "Batch Job X - Error 1050: Contention Detected",
            "from": "system@company.com",
            "to": "team@company.com", 
            "sentDateTime": datetime.now(timezone.utc),
            "receivedDateTime": datetime.now(timezone.utc),
            "hasAttachments": False,
            "conversationID": "conv-1234567890",
            "messageID": "msg-0987654321"
        },
        
        "knowledgeBaseMetadata": {
            "relevantSOPId": "SOP-CONTENTION-001",
            "files": [
                {
                    "fileName": "ADR_FAULT_example.TXT",
                    "fileType": "application/txt",
                    "fileSize": 204800,
                    "fileUrl": "s3://adr_fault_files/adr_fault_1234.txt"
                }
            ]
        },
        
        "remediationMetadata": {
            "expandability": "AI suggests restarting job B because Job A ran at the same time with a locked database resource...",
            "confidenceScore": 0.92,
            "remediationRecommendations": "## Recommended Actions\n1. Restart Job B\n2. Check database locks\n3. Monitor for contention",
            "aiRemediationApprovalStatus": "Pending",
            "aiRemediationApprovalRequired": True,
            "aiRemediationComments": "High confidence remediation available"
        },
        
        # Audit fields
        "createdAt": datetime.now(timezone.utc),
        "updatedAt": datetime.now(timezone.utc),
        "createdBy": "system",
        "updatedBy": "system", 
        "generation": 1
    }


# ADR Status Workflow Examples
ADR_STATUS_WORKFLOW = [
    "ABEND_REGISTERED",                    # 1. Initial state when abend notification received
    "LOG_EXTRACTION_INITIATED",           # 2. Log extraction process started  
    "MANUAL_INTERVENTION_REQUIRED",       # 3. Manual intervention needed (error state)
    "LOG_UPLOAD_TO_S3",                   # 4. Log uploaded to S3
    "PREPROCESSING_LOG_FILE",             # 5. Log file being preprocessed
    "AI_ANALYSIS_INITIATED",              # 6. AI analysis triggered
    "MANUAL_ANALYSIS_REQUIRED",           # 7. Manual analysis required (AI failed)
    "REMEDIATION_SUGGESTIONS_GENERATED",  # 8. AI suggestions generated
    "AUTOMATED_REMEDIATION_IN_PROGRESS",  # 9. Auto remediation executing
    "PENDING_MANUAL_APPROVAL",            # 10. Waiting for manual approval
    "VERIFICATION_IN_PROGRESS",           # 11. Verifying remediation results
    "RESOLVED"                            # 12. Final resolved state
]

# Severity Levels
SEVERITY_LEVELS = ["High", "Medium", "Low"]

# Common Query Patterns
QUERY_PATTERNS = {
    "by_adr_status": {
        "description": "Query records by ADR status for current day",
        "gsi": "ADRStatusIndex", 
        "hash_key": "adr_status",
        "range_key_pattern": "abended_at (ISO string, current day prefix)"
    },
    
    "by_severity": {
        "description": "Query records by severity level",
        "gsi": "SeverityIndex",
        "hash_key": "severity", 
        "range_key_pattern": "abended_at (ISO string)"
    },
    
    "by_job_name": {
        "description": "Query records by job name",
        "gsi": "JobNameIndex",
        "hash_key": "job_name",
        "range_key_pattern": "abended_at (ISO string)"
    },
    
    "by_domain_area": {
        "description": "Query records by domain area",
        "gsi": "DomainAreaIndex", 
        "hash_key": "domain_area",
        "range_key_pattern": "abended_at (ISO string)"
    },
    
    "by_abend_type": {
        "description": "Query records by abend type",
        "gsi": "AbendTypeIndex",
        "hash_key": "abend_type",
        "range_key_pattern": "abended_at (ISO string)"
    }
}

# Example tracking ID generation
def example_tracking_ids():
    """Examples of tracking ID format: ABEND_{jobname}_{ulid} - auto-generated"""
    # These would be generated by AbendDynamoTable.generate_tracking_id(job_name)
    return [
        "ABEND_WGMP110D_01ARZ3NDEKTSV4RRFFQ69G5FAV",
        "ABEND_CLAIMS01_01BX5ZZKBKACTAV9WEVGEMMVS0", 
        "ABEND_PAYROLL_01C1ED9P8Z8EXAMPLE12345678",
        "ABEND_REPORTS_01D2FE9Q9A9EXAMPLE87654321"
    ]


if __name__ == "__main__":
    print("=== ABEND Schema Examples ===\n")
    
    print("1. ADR Status Workflow:")
    for i, status in enumerate(ADR_STATUS_WORKFLOW, 1):
        print(f"   {i:2d}. {status}")
    
    print(f"\n2. Severity Levels: {', '.join(SEVERITY_LEVELS)}")
    
    print("\n3. Example Tracking IDs:")
    for tid in example_tracking_ids():
        print(f"   {tid}")
    
    print("\n4. Query Patterns:")
    for pattern_name, pattern_info in QUERY_PATTERNS.items():
        print(f"   {pattern_name}:")
        print(f"     - GSI: {pattern_info['gsi']}")
        print(f"     - Hash Key: {pattern_info['hash_key']}")
        print(f"     - Range Key: {pattern_info['range_key_pattern']}")
    
    print("\n5. Sample Payloads:")
    print("   - Basic payload: get_basic_abend_payload()")
    print("   - Detailed payload: get_detailed_abend_payload()")
