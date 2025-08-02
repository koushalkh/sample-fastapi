"""
Add Example Data to ABEND DynamoDB Table

This script creates and inserts sample ABEND records into the DynamoDB table
for testing and demonstration purposes.
"""

from datetime import datetime, timezone, timedelta
from app.schema.abend_dynamo import AbendDynamoTable
from app.models.abend import ADRStatusEnum, SeverityEnum


def create_sample_records():
    """Create sample ABEND records with various statuses and scenarios."""
    
    print("🚀 Adding Example Data to ABEND DynamoDB Table")
    print("=" * 50)
    
    # Sample data scenarios
    sample_records = [
        {
            "job_name": "WGMP110D",
            "job_id": "IYM98ID",
            "abended_minutes_ago": 30,
            "status": ADRStatusEnum.ABEND_REGISTERED,
            "severity": SeverityEnum.HIGH,
            "domain_area": "Claims Processing",
            "scenario": "New ABEND - just registered"
        },
        {
            "job_name": "CLAIMS01",
            "job_id": "CLM001",
            "abended_minutes_ago": 60,
            "status": ADRStatusEnum.LOG_EXTRACTION_INITIATED,
            "severity": SeverityEnum.MEDIUM,
            "domain_area": "Claims Processing",
            "scenario": "Log extraction in progress"
        },
        {
            "job_name": "PAYROLL",
            "job_id": "PAY001",
            "abended_minutes_ago": 90,
            "status": ADRStatusEnum.AI_ANALYSIS_INITIATED,
            "severity": SeverityEnum.LOW,
            "domain_area": "Human Resources",
            "scenario": "AI analysis started"
        },
        {
            "job_name": "REPORTS",
            "job_id": "RPT001",
            "abended_minutes_ago": 120,
            "status": ADRStatusEnum.REMEDIATION_SUGGESTIONS_GENERATED,
            "severity": SeverityEnum.HIGH,
            "domain_area": "Business Intelligence",
            "scenario": "AI suggestions ready"
        },
        {
            "job_name": "BILLING",
            "job_id": "BIL001",
            "abended_minutes_ago": 180,
            "status": ADRStatusEnum.PENDING_MANUAL_APPROVAL,
            "severity": SeverityEnum.MEDIUM,
            "domain_area": "Financial Services",
            "scenario": "Awaiting manual approval"
        },
        {
            "job_name": "INVENTORY",
            "job_id": "INV001",
            "abended_minutes_ago": 240,
            "status": ADRStatusEnum.VERIFICATION_IN_PROGRESS,
            "severity": SeverityEnum.LOW,
            "domain_area": "Supply Chain",
            "scenario": "Verifying remediation"
        },
        {
            "job_name": "CUSTOMER",
            "job_id": "CUS001",
            "abended_minutes_ago": 300,
            "status": ADRStatusEnum.RESOLVED,
            "severity": SeverityEnum.HIGH,
            "domain_area": "Customer Service",
            "scenario": "Successfully resolved"
        },
        {
            "job_name": "SECURITY",
            "job_id": "SEC001",
            "abended_minutes_ago": 15,
            "status": ADRStatusEnum.MANUAL_INTERVENTION_REQUIRED,
            "severity": SeverityEnum.HIGH,
            "domain_area": "Information Security",
            "scenario": "Manual intervention needed"
        }
    ]
    
    created_records = []
    
    for i, record_data in enumerate(sample_records, 1):
        print(f"\n📋 Creating Record {i}/8: {record_data['scenario']}")
        
        # Calculate abended_at time
        abended_at = datetime.now(timezone.utc) - timedelta(minutes=record_data['abended_minutes_ago'])
        
        # Generate tracking ID
        tracking_id = AbendDynamoTable.generate_tracking_id(record_data['job_name'])
        
        # Create the record
        abend_record = AbendDynamoTable(
            tracking_id=tracking_id,
            abended_at=abended_at,
            
            # Basic job information
            job_id=record_data['job_id'],
            job_name=record_data['job_name'],
            order_id=f"ORD{i:03d}",
            incident_number=f"INC{10000 + i}",
            fa_id=f"F{70000 + i}",
            domain_area=record_data['domain_area'],
            
            # ABEND specific information
            abend_type="EFX" if i % 2 == 0 else "GG",
            abend_step=f"{i:02d}",
            abend_return_code=str(10 + i),
            abend_reason=f"Error {1000 + i}: Sample error for testing",
            
            # Status and severity
            adr_status=record_data['status'].value,
            severity=record_data['severity'].value,
            
            # Performance metrics (sample data)
            perf_log_extraction_time=f"{150 + i*10}s",
            perf_ai_analysis_time=f"{200 + i*15}s",
            perf_remediation_time=f"{100 + i*5}s",
            perf_total_automated_time=f"{450 + i*30}s",
            
            # Log extraction metadata
            log_extraction_run_id=f"RUN{1000000 + i}",
            log_extraction_retries=i % 3,  # 0, 1, or 2 retries
            
            # Audit fields
            created_by="sample_data_script",
            updated_by="sample_data_script",
            generation=1
        )
        
        # Add email metadata for some records
        if i % 2 == 0:
            email_data = {
                "subject": f"ABEND Alert - {record_data['job_name']} Job Failed",
                "from": "alerts@company.com",
                "to": "operations@company.com",
                "sentDateTime": abended_at.isoformat(),
                "receivedDateTime": (abended_at + timedelta(seconds=30)).isoformat(),
                "hasAttachments": i % 4 == 0,
                "conversationID": f"conv-{tracking_id}",
                "messageID": f"msg-{tracking_id}"
            }
            abend_record.set_email_metadata(email_data)
        
        # Add knowledge base metadata for some records
        if i % 3 == 0:
            kb_data = {
                "relevantSOPId": f"SOP-{record_data['job_name']}-001",
                "files": [
                    {
                        "fileName": f"ADR_FAULT_{record_data['job_name']}.TXT",
                        "fileType": "application/txt",
                        "fileSize": 204800 + i * 1000,
                        "fileUrl": f"s3://adr-fault-files/fault_{tracking_id.lower()}.txt"
                    }
                ]
            }
            abend_record.set_knowledge_base_metadata(kb_data)
        
        # Add remediation metadata for records with suggestions or higher status
        if record_data['status'] in [
            ADRStatusEnum.REMEDIATION_SUGGESTIONS_GENERATED,
            ADRStatusEnum.PENDING_MANUAL_APPROVAL,
            ADRStatusEnum.VERIFICATION_IN_PROGRESS,
            ADRStatusEnum.RESOLVED
        ]:
            remediation_data = {
                "expandability": f"AI analysis suggests that {record_data['job_name']} failed due to resource contention. Recommended action: restart with increased memory allocation.",
                "confidenceScore": 0.85 + (i * 0.02),  # Varying confidence scores
                "remediationRecommendations": f"## Recommended Actions for {record_data['job_name']}\n\n1. Check system resources\n2. Restart job with increased memory\n3. Monitor for similar issues\n4. Update job configuration if needed",
                "aiRemediationApprovalStatus": "Approved" if record_data['status'] == ADRStatusEnum.RESOLVED else "Pending",
                "aiRemediationApprovalRequired": record_data['severity'] == SeverityEnum.HIGH,
                "aiRemediationComments": f"High confidence remediation available for {record_data['job_name']}"
            }
            abend_record.set_remediation_metadata(remediation_data)
        
        try:
            # Save the record to DynamoDB
            abend_record.save()
            created_records.append(abend_record)
            
            print(f"   ✅ Created: {tracking_id}")
            print(f"   📊 Status: {record_data['status'].value}")
            print(f"   🚨 Severity: {record_data['severity'].value}")
            print(f"   🕒 Abended: {abended_at.strftime('%Y-%m-%d %H:%M:%S')} UTC")
            
        except Exception as e:
            print(f"   ❌ Failed to create record: {e}")
    
    return created_records


def query_sample_data():
    """Query and display the sample data to verify it was created correctly."""
    
    print("\n\n🔍 Querying Sample Data")
    print("=" * 50)
    
    try:
        # Query by severity (High)
        print(f"\n📊 High Severity Records:")
        high_severity_records = list(AbendDynamoTable.severity_index.query(
            hash_key=SeverityEnum.HIGH.value,
            limit=10
        ))
        
        for record in high_severity_records:
            print(f"   🔴 {record.tracking_id} - {record.adr_status} - {record.job_name}")
        
        # Query by status (ABEND_REGISTERED)
        print(f"\n🆕 Recently Registered ABENDs:")
        registered_records = list(AbendDynamoTable.adr_status_index.query(
            hash_key=ADRStatusEnum.ABEND_REGISTERED.value,
            limit=10
        ))
        
        for record in registered_records:
            print(f"   🆕 {record.tracking_id} - {record.job_name} - {record.domain_area}")
        
        # Query by job name
        print(f"\n💼 Claims Processing Jobs:")
        claims_records = list(AbendDynamoTable.domain_area_index.query(
            hash_key="Claims Processing",
            limit=10
        ))
        
        for record in claims_records:
            print(f"   💼 {record.tracking_id} - {record.job_name} - {record.adr_status}")
            
    except Exception as e:
        print(f"   ❌ Query failed: {e}")
        print("   💡 Note: This might happen if running against LocalStack or if table doesn't exist yet")


def main():
    """Main function to create sample data and verify it."""
    
    print("🗄️  ABEND DynamoDB Sample Data Creator")
    print("=" * 60)
    print("This script will create sample ABEND records for testing.")
    print("Make sure your DynamoDB connection is properly configured.\n")
    
    try:
        # Create sample records
        created_records = create_sample_records()
        
        print(f"\n✅ Successfully created {len(created_records)} sample records!")
        
        # Query and display sample data
        query_sample_data()
        
        print(f"\n🎉 Sample data creation completed!")
        print("\nYou can now:")
        print("1. Test your API endpoints with this data")
        print("2. Run queries against different GSIs")
        print("3. Test status updates and workflows")
        print("4. Verify datetime handling and filtering")
        
    except Exception as e:
        print(f"\n❌ Error during sample data creation: {e}")
        print("\n💡 Troubleshooting tips:")
        print("1. Check if DynamoDB table exists")
        print("2. Verify AWS credentials are configured")
        print("3. Ensure DynamoDB service is running (LocalStack if local)")
        print("4. Check network connectivity to DynamoDB")


if __name__ == "__main__":
    main()
