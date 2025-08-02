"""
Query ABEND DynamoDB Table Data

This script queries and displays data from the ABEND DynamoDB table
to verify the sample data and test different query patterns.
"""

from app.schema.abend_dynamo import AbendDynamoTable
from app.models.abend import ADRStatusEnum, SeverityEnum
from datetime import datetime, timezone


def display_all_records():
    """Display all records in the table."""
    
    print("📋 All ABEND Records")
    print("=" * 80)
    
    try:
        records = list(AbendDynamoTable.scan())
        
        if not records:
            print("   No records found in the table.")
            return
        
        print(f"Found {len(records)} records:\n")
        
        for i, record in enumerate(records, 1):
            print(f"{i:2d}. 🆔 {record.tracking_id}")
            print(f"    💼 Job: {record.job_name} ({record.job_id})")
            print(f"    📊 Status: {record.adr_status}")
            print(f"    🚨 Severity: {record.severity}")
            print(f"    🏢 Domain: {record.domain_area}")
            print(f"    🕒 Abended: {record.abended_at.strftime('%Y-%m-%d %H:%M:%S')} UTC")
            
            # Show additional details if available
            if hasattr(record, 'incident_number') and record.incident_number:
                print(f"    🎫 Incident: {record.incident_number}")
            
            if hasattr(record, 'email_metadata') and record.email_metadata:
                print(f"    📧 Email: {record.email_metadata.get('subject', 'N/A')}")
            
            print()
            
    except Exception as e:
        print(f"❌ Error scanning table: {e}")


def query_by_status():
    """Query records by different ADR statuses."""
    
    print("🔍 Query by ADR Status")
    print("=" * 50)
    
    # Test different statuses
    statuses_to_test = [
        ADRStatusEnum.ABEND_REGISTERED,
        ADRStatusEnum.LOG_EXTRACTION_INITIATED,
        ADRStatusEnum.PENDING_MANUAL_APPROVAL,
        ADRStatusEnum.RESOLVED
    ]
    
    for status in statuses_to_test:
        try:
            # Note: This would work if GSIs are properly created and active
            print(f"\n📊 Status: {status.value}")
            
            # For now, let's scan and filter since GSI might not be ready
            all_records = list(AbendDynamoTable.scan())
            filtered_records = [r for r in all_records if r.adr_status == status.value]
            
            if filtered_records:
                print(f"   Found {len(filtered_records)} record(s):")
                for record in filtered_records:
                    print(f"   - {record.tracking_id} | {record.job_name} | {record.severity}")
            else:
                print("   No records found with this status")
                
        except Exception as e:
            print(f"   ❌ Query failed: {e}")


def query_by_severity():
    """Query records by severity level."""
    
    print("\n🚨 Query by Severity")
    print("=" * 50)
    
    for severity in SeverityEnum:
        try:
            print(f"\n📈 Severity: {severity.value}")
            
            # Scan and filter by severity
            all_records = list(AbendDynamoTable.scan())
            filtered_records = [r for r in all_records if r.severity == severity.value]
            
            if filtered_records:
                print(f"   Found {len(filtered_records)} record(s):")
                for record in filtered_records:
                    abended_time = record.abended_at.strftime('%H:%M')
                    print(f"   - {record.job_name} | {record.adr_status} | {abended_time}")
            else:
                print("   No records found with this severity")
                
        except Exception as e:
            print(f"   ❌ Query failed: {e}")


def query_by_domain():
    """Query records by domain area."""
    
    print("\n🏢 Query by Domain Area")
    print("=" * 50)
    
    try:
        # Get all unique domain areas
        all_records = list(AbendDynamoTable.scan())
        domains = set(r.domain_area for r in all_records if r.domain_area)
        
        for domain in sorted(domains):
            print(f"\n🏢 Domain: {domain}")
            
            domain_records = [r for r in all_records if r.domain_area == domain]
            print(f"   Found {len(domain_records)} record(s):")
            
            for record in domain_records:
                print(f"   - {record.job_name} | {record.adr_status}")
                
    except Exception as e:
        print(f"❌ Error querying by domain: {e}")


def show_record_details(tracking_id: str):
    """Show detailed information for a specific record."""
    
    print(f"\n🔍 Record Details: {tracking_id}")
    print("=" * 80)
    
    try:
        # Find the record by scanning (since we don't have the exact abended_at)
        all_records = list(AbendDynamoTable.scan())
        record = next((r for r in all_records if r.tracking_id == tracking_id), None)
        
        if not record:
            print("   Record not found")
            return
        
        print(f"🆔 Tracking ID: {record.tracking_id}")
        print(f"💼 Job ID: {record.job_id}")
        print(f"💼 Job Name: {record.job_name}")
        print(f"📊 Status: {record.adr_status}")
        print(f"🚨 Severity: {record.severity}")
        print(f"🏢 Domain: {record.domain_area}")
        print(f"🕒 Abended At: {record.abended_at}")
        print(f"🕒 Created At: {record.created_at}")
        print(f"🕒 Updated At: {record.updated_at}")
        
        # Show additional fields if they exist
        if hasattr(record, 'incident_number') and record.incident_number:
            print(f"🎫 Incident: {record.incident_number}")
        
        if hasattr(record, 'order_id') and record.order_id:
            print(f"📋 Order ID: {record.order_id}")
        
        if hasattr(record, 'fa_id') and record.fa_id:
            print(f"🔧 FA ID: {record.fa_id}")
        
        if hasattr(record, 'abend_reason') and record.abend_reason:
            print(f"❌ Reason: {record.abend_reason}")
        
        # Show performance metrics
        if hasattr(record, 'perf_log_extraction_time') and record.perf_log_extraction_time:
            print(f"\n⚡ Performance Metrics:")
            print(f"   Log Extraction: {record.perf_log_extraction_time}")
            if hasattr(record, 'perf_ai_analysis_time') and record.perf_ai_analysis_time:
                print(f"   AI Analysis: {record.perf_ai_analysis_time}")
            if hasattr(record, 'perf_total_automated_time') and record.perf_total_automated_time:
                print(f"   Total Automated: {record.perf_total_automated_time}")
        
        # Show complex metadata
        if hasattr(record, 'email_metadata') and record.email_metadata:
            print(f"\n📧 Email Metadata:")
            print(f"   Subject: {record.email_metadata.get('subject', 'N/A')}")
            print(f"   From: {record.email_metadata.get('from', 'N/A')}")
        
        if hasattr(record, 'remediation_metadata') and record.remediation_metadata:
            print(f"\n🔧 Remediation Metadata:")
            print(f"   Confidence: {record.remediation_metadata.get('confidenceScore', 'N/A')}")
            print(f"   Status: {record.remediation_metadata.get('aiRemediationApprovalStatus', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Error getting record details: {e}")


def main():
    """Main function to display and query ABEND data."""
    
    print("📊 ABEND DynamoDB Data Explorer")
    print("=" * 60)
    print("Exploring existing data in the ABEND table...\n")
    
    # Display all records
    display_all_records()
    
    # Query by different criteria
    query_by_status()
    query_by_severity()
    query_by_domain()
    
    # Show details for the first record if any exist
    try:
        records = list(AbendDynamoTable.scan(limit=1))
        if records:
            show_record_details(records[0].tracking_id)
    except Exception as e:
        print(f"Could not show record details: {e}")
    
    print(f"\n🎉 Data exploration completed!")
    print("\nThe table contains sample ABEND records with various statuses.")
    print("You can now test your API endpoints against this data.")


if __name__ == "__main__":
    main()
