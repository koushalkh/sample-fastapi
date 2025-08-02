"""
Simple DynamoDB Table Test

This script tests basic DynamoDB operations with the ABEND table.
"""

from app.schema.abend_dynamo import AbendDynamoTable
from app.models.abend import ADRStatusEnum, SeverityEnum
from datetime import datetime, timezone


def test_table_exists():
    """Test if the table exists and basic operations work."""
    
    print("🧪 Testing DynamoDB Table Operations")
    print("=" * 50)
    
    try:
        # Test 1: Check if table exists
        print("1️⃣  Testing table existence...")
        exists = AbendDynamoTable.exists()
        print(f"   Table exists: {exists}")
        
        if not exists:
            print("   Creating table...")
            AbendDynamoTable.create_table(
                read_capacity_units=5,
                write_capacity_units=5,
                wait=True
            )
            print("   ✅ Table created!")
        
        # Test 2: Create a test record
        print("\n2️⃣  Testing record creation...")
        tracking_id = AbendDynamoTable.generate_tracking_id("TEST01")
        abended_at = datetime.now(timezone.utc)
        
        test_record = AbendDynamoTable(
            tracking_id=tracking_id,
            abended_at=abended_at,
            job_id="TEST001",
            job_name="TEST01",
            adr_status=ADRStatusEnum.ABEND_REGISTERED.value,
            severity=SeverityEnum.MEDIUM.value,
            domain_area="Testing"
        )
        
        test_record.save()
        print(f"   ✅ Test record created: {tracking_id}")
        
        # Test 3: Retrieve the record
        print("\n3️⃣  Testing record retrieval...")
        retrieved = AbendDynamoTable.get(tracking_id, abended_at)
        print(f"   ✅ Retrieved: {retrieved.job_name} - {retrieved.adr_status}")
        
        # Test 4: Update the record
        print("\n4️⃣  Testing record update...")
        retrieved.adr_status = ADRStatusEnum.LOG_EXTRACTION_INITIATED.value
        retrieved.save()
        print(f"   ✅ Updated status to: {retrieved.adr_status}")
        
        # Test 5: Simple scan to count records
        print("\n5️⃣  Testing table scan...")
        count = 0
        for record in AbendDynamoTable.scan(limit=10):
            count += 1
        print(f"   ✅ Found {count} record(s) in table")
        
        # Test 6: Clean up
        print("\n6️⃣  Cleaning up test record...")
        test_record.delete()
        print("   ✅ Test record deleted")
        
        print(f"\n🎉 All tests passed! DynamoDB table is working correctly.")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        print(f"Error type: {type(e).__name__}")
        
        # Print more debugging info
        try:
            from app.core.config import settings
            print(f"\nDebug info:")
            print(f"  AWS Region: {settings.aws_region}")
            print(f"  DynamoDB Endpoint: {getattr(settings, 'dynamodb_endpoint', 'Not set')}")
            print(f"  Environment: {settings.environment}")
        except Exception as debug_e:
            print(f"  Could not get debug info: {debug_e}")
        
        return False


if __name__ == "__main__":
    print("🔧 Simple DynamoDB Test for ABEND Table")
    print("=" * 50)
    print("This script tests basic DynamoDB operations.\n")
    
    if test_table_exists():
        print("\n✅ DynamoDB is configured correctly and ready for use!")
        print("\nNext steps:")
        print("1. Run 'python examples/add_sample_data.py' to add sample data")
        print("2. Test GSI queries")
    else:
        print("\n❌ DynamoDB test failed. Please check your configuration.")
        print("\nTroubleshooting:")
        print("1. Check if LocalStack is running (if using local DynamoDB)")
        print("2. Verify AWS credentials are configured")
        print("3. Check network connectivity")
        print("4. Verify environment variables are set correctly")
