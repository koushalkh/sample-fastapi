"""
Create ABEND DynamoDB Table and Indexes

This script creates the DynamoDB table with all required Global Secondary Indexes
for the ABEND system.
"""

from app.schema.abend_dynamo import AbendDynamoTable
import time


def create_table_and_indexes():
    """Create the DynamoDB table with all GSIs."""
    
    print("🏗️  Creating ABEND DynamoDB Table and Indexes")
    print("=" * 60)
    
    try:
        # Check if table already exists
        if AbendDynamoTable.exists():
            print("📋 Table already exists!")
            
            # Get table description
            table_desc = AbendDynamoTable.describe_table()
            print(f"   Table Name: {table_desc['Table']['TableName']}")
            print(f"   Table Status: {table_desc['Table']['TableStatus']}")
            print(f"   Item Count: {table_desc['Table']['ItemCount']}")
            
            # List Global Secondary Indexes
            if 'GlobalSecondaryIndexes' in table_desc['Table']:
                print(f"\n📊 Global Secondary Indexes:")
                for gsi in table_desc['Table']['GlobalSecondaryIndexes']:
                    print(f"   - {gsi['IndexName']}: {gsi['IndexStatus']}")
            
            return True
            
    except Exception as e:
        print(f"📋 Table doesn't exist yet. Creating new table...")
    
    try:
        # Create the table
        print("🚀 Creating table with GSIs...")
        
        # This will create the table with all defined GSIs
        AbendDynamoTable.create_table(
            read_capacity_units=5,
            write_capacity_units=5,
            wait=True  # Wait for table to be active
        )
        
        print("✅ Table created successfully!")
        
        # Wait a bit for GSIs to be active
        print("⏳ Waiting for Global Secondary Indexes to become active...")
        time.sleep(10)
        
        # Verify table creation
        table_desc = AbendDynamoTable.describe_table()
        print(f"\n📋 Table Details:")
        print(f"   Table Name: {table_desc['Table']['TableName']}")
        print(f"   Table Status: {table_desc['Table']['TableStatus']}")
        
        # List Global Secondary Indexes
        if 'GlobalSecondaryIndexes' in table_desc['Table']:
            print(f"\n📊 Global Secondary Indexes:")
            for gsi in table_desc['Table']['GlobalSecondaryIndexes']:
                print(f"   - {gsi['IndexName']}: {gsi['IndexStatus']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to create table: {e}")
        print("\n💡 Troubleshooting tips:")
        print("1. Check AWS credentials are configured")
        print("2. Ensure proper permissions for DynamoDB")
        print("3. Verify DynamoDB service is running (LocalStack if local)")
        print("4. Check if table name conflicts exist")
        return False


def test_table_operations():
    """Test basic table operations."""
    
    print(f"\n🧪 Testing Table Operations")
    print("=" * 40)
    
    try:
        # Test creating a simple record
        from datetime import datetime, timezone
        from app.models.abend import ADRStatusEnum, SeverityEnum
        
        tracking_id = AbendDynamoTable.generate_tracking_id("TEST01")
        
        test_record = AbendDynamoTable(
            tracking_id=tracking_id,
            abended_at=datetime.now(timezone.utc),
            job_id="TEST001",
            job_name="TEST01",
            adr_status=ADRStatusEnum.ABEND_REGISTERED.value,
            severity=SeverityEnum.MEDIUM.value,
            domain_area="Testing"
        )
        
        # Save test record
        test_record.save()
        print(f"✅ Test record created: {tracking_id}")
        
        # Retrieve test record
        retrieved = AbendDynamoTable.get(tracking_id, test_record.abended_at)
        print(f"✅ Test record retrieved: {retrieved.job_name}")
        
        # Test GSI query
        test_records = list(AbendDynamoTable.adr_status_index.query(
            hash_key=ADRStatusEnum.ABEND_REGISTERED.value,
            limit=1
        ))
        
        if test_records:
            print(f"✅ GSI query successful: Found {len(test_records)} record(s)")
        
        # Clean up test record
        test_record.delete()
        print(f"✅ Test record cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Table operation test failed: {e}")
        return False


def main():
    """Main function to create table and test operations."""
    
    print("🗄️  ABEND DynamoDB Table Setup")
    print("=" * 50)
    print("This script will create the DynamoDB table and all required indexes.\n")
    
    # Create table and indexes
    if create_table_and_indexes():
        print(f"\n🎉 Table setup completed successfully!")
        
        # Test basic operations
        if test_table_operations():
            print(f"\n✅ All tests passed! Table is ready for use.")
            print("\nNext steps:")
            print("1. Run 'python examples/add_sample_data.py' to add sample data")
            print("2. Test your API endpoints")
            print("3. Run queries against the GSIs")
        else:
            print(f"\n⚠️  Table created but tests failed. Check configuration.")
    else:
        print(f"\n❌ Failed to set up table. Please check configuration.")


if __name__ == "__main__":
    main()
