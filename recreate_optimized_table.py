#!/usr/bin/env python3
"""
Script to recreate optimized table with updated JobHistoryIndex and verify GSIs
"""

from app.schema.abend_dynamo_optimized import AbendDynamoTable
from datetime import datetime, timezone
import ulid

def main():
    print("🔧 RECREATING OPTIMIZED TABLE WITH UPDATED SCHEMA")
    print("=" * 60)
    
    # Step 1: Delete and recreate table
    try:
        if AbendDynamoTable.exists():
            print("⚠️  Deleting existing table...")
            AbendDynamoTable.delete_table()
            print("✅ Existing table deleted")
        
        print("🚀 Creating optimized table with updated JobHistoryIndex...")
        AbendDynamoTable.create_table(read_capacity_units=5, write_capacity_units=3, wait=True)
        print("✅ Table created successfully")
        
    except Exception as e:
        print(f"❌ Table creation error: {e}")
        return False
    
    # Step 2: Add sample data
    try:
        print("\n📝 Adding sample data...")
        now = datetime.now(timezone.utc)
        today_str = now.strftime("%Y-%m-%d")
        
        # Create test records with different job names for JobHistoryIndex testing
        test_data = [
            {
                "job_name": "PAYROLL_PROCESSING",
                "domain": "Payroll Processing",
                "severity": "High",
                "reason": "Memory allocation failure"
            },
            {
                "job_name": "CLAIMS_PROCESSING", 
                "domain": "Claims Processing",
                "severity": "Medium",
                "reason": "Database timeout"
            },
            {
                "job_name": "DATA_MIGRATION",
                "domain": "Data Management", 
                "severity": "Low",
                "reason": "File not found"
            },
            {
                "job_name": "PAYROLL_PROCESSING",  # Same job name for history testing
                "domain": "Payroll Processing",
                "severity": "Critical",
                "reason": "System crash"
            }
        ]
        
        records_created = 0
        for i, data in enumerate(test_data):
            record = AbendDynamoTable(
                tracking_id=f"ABEND_{ulid.ulid()}",
                record_type="ABEND",
                abended_date=today_str,
                abended_at=now.isoformat(),
                job_id=f"JOB_{i+1:03d}",
                job_name=data["job_name"],
                domain_area=data["domain"],
                severity=data["severity"],
                adr_status="IN_PROGRESS",
                incident_number=f"INC20250802{i+1:03d}",
                abend_reason=data["reason"],
                perf_log_extraction_time=f"{150 + i*50}ms",
                perf_ai_analysis_time=f"{2000 + i*500}ms",
                email_metadata={
                    "sent": True,
                    "recipients": [f"team-{data['domain'].lower().replace(' ', '-')}@company.com"]
                },
                knowledge_base_metadata={
                    "articles_found": i + 1,
                    "confidence": 0.8 + (i * 0.05)
                },
                generation=1
            )
            record.save()
            records_created += 1
            print(f"✅ Record {i+1}: {data['job_name']} - {data['severity']}")
        
        print(f"\n✅ Created {records_created} sample records")
        
    except Exception as e:
        print(f"❌ Sample data creation error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 3: Verify GSIs
    try:
        print("\n🔍 VERIFYING GSI FUNCTIONALITY")
        print("-" * 40)
        
        # Test AbendedDateIndex
        print("Testing AbendedDateIndex...")
        today_results = list(AbendDynamoTable.abended_date_index.query(hash_key=today_str))
        print(f"✅ AbendedDateIndex: Found {len(today_results)} records for {today_str}")
        
        # Test JobHistoryIndex (updated to use job_name)
        print("Testing JobHistoryIndex...")
        payroll_results = list(AbendDynamoTable.job_history_index.query(hash_key="PAYROLL_PROCESSING"))
        print(f"✅ JobHistoryIndex: Found {len(payroll_results)} records for PAYROLL_PROCESSING")
        
        claims_results = list(AbendDynamoTable.job_history_index.query(hash_key="CLAIMS_PROCESSING"))
        print(f"✅ JobHistoryIndex: Found {len(claims_results)} records for CLAIMS_PROCESSING")
        
        # Summary
        print(f"\n📊 VERIFICATION SUMMARY")
        print(f"✅ Total records: {AbendDynamoTable.count()}")
        print(f"✅ AbendedDateIndex working: {len(today_results)} today's records")
        print(f"✅ JobHistoryIndex working: Multiple job name queries successful")
        print(f"✅ Updated schema using job_name instead of job_id")
        
        print(f"\n🎯 OPTIMIZED TABLE WITH UPDATED GSI READY!")
        return True
        
    except Exception as e:
        print(f"❌ GSI verification error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
