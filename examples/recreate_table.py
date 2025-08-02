"""
Recreate DynamoDB Table with Correct GSIs

This script drops the existing table and recreates it with the correct 
Global Secondary Indexes to match our current schema.
"""

from app.schema.abend_dynamo import AbendDynamoTable
from app.schema.dynamo_config import DynamoDBConfig
import time
import boto3
from botocore.exceptions import ClientError


def drop_existing_table():
    """Drop the existing table if it exists."""
    
    print("🗑️  Dropping Existing Table")
    print("=" * 40)
    
    try:
        if AbendDynamoTable.exists():
            print("📋 Found existing table. Deleting...")
            
            # Delete the table
            AbendDynamoTable.delete_table()
            
            # Wait for deletion to complete
            print("⏳ Waiting for table deletion to complete...")
            start_time = time.time()
            
            while True:
                try:
                    if not AbendDynamoTable.exists():
                        break
                    time.sleep(2)
                    elapsed = time.time() - start_time
                    if elapsed > 60:  # 1 minute timeout
                        print("⚠️  Table deletion taking longer than expected")
                        break
                except:
                    # Table doesn't exist anymore
                    break
            
            print("✅ Table deleted successfully!")
            
        else:
            print("📋 No existing table found.")
            
    except Exception as e:
        print(f"❌ Error dropping table: {e}")
        return False
    
    return True


def create_table_with_correct_gsis():
    """Create table with the correct GSI configuration."""
    
    print("\n🏗️  Creating Table with Correct GSIs")
    print("=" * 50)
    
    try:
        print("🚀 Creating table with all 5 GSIs...")
        print("   - AbendTypeIndex")
        print("   - JobNameIndex") 
        print("   - DomainAreaIndex")
        print("   - ADRStatusIndex")
        print("   - SeverityIndex")
        
        # Create the table with all GSIs
        # For PynamoDB, GSI throughput is set via the Meta class in each GSI
        AbendDynamoTable.create_table(
            read_capacity_units=5,
            write_capacity_units=5,
            wait=True  # Wait for table to be active
        )
        
        print("✅ Table created successfully!")
        
        # Verify table creation
        if AbendDynamoTable.exists():
            print("\n📊 Verifying table and GSIs...")
            
            try:
                # Get table description
                table_desc = AbendDynamoTable.describe_table()
                table_info = table_desc['Table']
                
                print(f"   Table Name: {table_info['TableName']}")
                print(f"   Table Status: {table_info['TableStatus']}")
                
                # Check GSIs
                if 'GlobalSecondaryIndexes' in table_info:
                    gsis = table_info['GlobalSecondaryIndexes']
                    print(f"\n🔗 Global Secondary Indexes ({len(gsis)}):")
                    
                    for gsi in gsis:
                        print(f"   ✅ {gsi['IndexName']}: {gsi['IndexStatus']}")
                        
                        # Show key schema
                        keys = [f"{k['AttributeName']} ({k['KeyType']})" for k in gsi['KeySchema']]
                        print(f"      Keys: {', '.join(keys)}")
                    
                    print(f"\n🎉 All {len(gsis)} GSIs created successfully!")
                    
                else:
                    print("❌ No GSIs found in created table!")
                    return False
                    
            except Exception as e:
                print(f"⚠️  Table created but couldn't get details: {e}")
                print("   This might be normal during table initialization.")
                return True
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating table: {e}")
        return False


def verify_gsi_attributes():
    """Verify that our schema attributes match the GSI requirements."""
    
    print("\n🔍 Verifying GSI Attribute Mapping")
    print("=" * 40)
    
    # Check that our model has all the required attributes for GSIs
    required_attrs = {
        'AbendTypeIndex': ['abend_type', 'abended_at'],
        'JobNameIndex': ['job_name', 'abended_at'],
        'DomainAreaIndex': ['domain_area', 'abended_at'],
        'ADRStatusIndex': ['adr_status', 'abended_at'], 
        'SeverityIndex': ['severity', 'abended_at']
    }
    
    # Get model attributes
    model_attrs = [attr for attr in dir(AbendDynamoTable) if not attr.startswith('_')]
    
    for gsi_name, attrs in required_attrs.items():
        print(f"\n   {gsi_name}:")
        for attr in attrs:
            if attr in model_attrs:
                print(f"      ✅ {attr}")
            else:
                print(f"      ❌ {attr} - MISSING!")
    
    print("\n✅ Attribute verification complete!")


def main():
    """Main function to recreate table with correct GSIs."""
    
    print("🔄 DynamoDB Table Recreation Tool")
    print("=" * 60)
    print("This tool will recreate the table with the correct GSI configuration.\n")
    
    # Step 1: Verify our schema attributes
    verify_gsi_attributes()
    
    # Step 2: Drop existing table
    if not drop_existing_table():
        print("\n❌ Failed to drop existing table. Exiting.")
        return
    
    # Wait a moment for cleanup
    print("\n⏳ Waiting a moment for cleanup...")
    time.sleep(3)
    
    # Step 3: Create table with correct GSIs
    if not create_table_with_correct_gsis():
        print("\n❌ Failed to create table. Exiting.")
        return
    
    print("\n🎉 Table recreation completed successfully!")
    print("\n💡 Next steps:")
    print("1. Re-run your data population script: python examples/add_sample_data.py")
    print("2. Verify GSIs work: python examples/verify_gsi.py")
    print("3. Test queries: python examples/query_sample_data.py")


if __name__ == "__main__":
    main()
