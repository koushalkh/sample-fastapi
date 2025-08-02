"""
Verify DynamoDB GSI Status and Functionality

This script checks the status of Global Secondary Indexes and tests their functionality.
"""

from app.schema.abend_dynamo import AbendDynamoTable
from app.models.abend import ADRStatusEnum, SeverityEnum
import boto3
from botocore.exceptions import ClientError


def check_table_and_gsi_status():
    """Check the table and GSI status using boto3."""
    
    print("🔍 Checking Table and GSI Status")
    print("=" * 60)
    
    try:
        # Get DynamoDB client from the schema configuration
        from app.schema.dynamo_config import DynamoDBConfig
        kwargs = DynamoDBConfig.get_connection_kwargs()
        
        # Create DynamoDB client
        if 'host' in kwargs:
            # Local DynamoDB (LocalStack)
            dynamodb = boto3.client(
                'dynamodb',
                region_name=kwargs['region'],
                endpoint_url=kwargs['host'],
                aws_access_key_id=kwargs['aws_access_key_id'],
                aws_secret_access_key=kwargs['aws_secret_access_key']
            )
        else:
            # AWS DynamoDB
            dynamodb = boto3.client('dynamodb', region_name=kwargs['region'])
        
        # Get table description
        table_name = f"{DynamoDBConfig.get_table_name_prefix()}abend-records"
        print(f"📋 Table Name: {table_name}")
        
        try:
            response = dynamodb.describe_table(TableName=table_name)
            table = response['Table']
            
            print(f"📊 Table Status: {table['TableStatus']}")
            print(f"📦 Item Count: {table['ItemCount']}")
            print(f"💾 Table Size: {table['TableSizeBytes']} bytes")
            
            # Check Global Secondary Indexes
            if 'GlobalSecondaryIndexes' in table:
                print(f"\n🔗 Global Secondary Indexes ({len(table['GlobalSecondaryIndexes'])}):")
                for gsi in table['GlobalSecondaryIndexes']:
                    print(f"   📌 {gsi['IndexName']}")
                    print(f"      Status: {gsi['IndexStatus']}")
                    print(f"      Items: {gsi.get('ItemCount', 'N/A')}")
                    print(f"      Size: {gsi.get('IndexSizeBytes', 'N/A')} bytes")
                    
                    # Show key schema
                    print(f"      Keys: ", end="")
                    for key in gsi['KeySchema']:
                        print(f"{key['AttributeName']} ({key['KeyType']}) ", end="")
                    print()
                    print()
            else:
                print("\n❌ No Global Secondary Indexes found!")
                
        except ClientError as e:
            print(f"❌ Error describing table: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Error setting up DynamoDB client: {e}")
        return False
    
    return True


def test_gsi_queries():
    """Test GSI queries to verify they're working."""
    
    print("🧪 Testing GSI Queries")
    print("=" * 40)
    
    test_results = {}
    
    # Test 1: ADR Status Index
    print("\n1️⃣  Testing ADRStatusIndex...")
    try:
        status = ADRStatusEnum.ABEND_REGISTERED.value
        results = list(AbendDynamoTable.adr_status_index.query(
            hash_key=status,
            limit=5
        ))
        print(f"   ✅ Found {len(results)} records with status '{status}'")
        test_results['adr_status'] = len(results)
        
        if results:
            for record in results[:2]:  # Show first 2
                print(f"      - {record.tracking_id} | {record.job_name}")
                
    except Exception as e:
        print(f"   ❌ ADRStatusIndex query failed: {e}")
        test_results['adr_status'] = 'FAILED'
    
    # Test 2: Severity Index
    print("\n2️⃣  Testing SeverityIndex...")
    try:
        severity = SeverityEnum.HIGH.value
        results = list(AbendDynamoTable.severity_index.query(
            hash_key=severity,
            limit=5
        ))
        print(f"   ✅ Found {len(results)} records with severity '{severity}'")
        test_results['severity'] = len(results)
        
        if results:
            for record in results[:2]:  # Show first 2
                print(f"      - {record.tracking_id} | {record.job_name}")
                
    except Exception as e:
        print(f"   ❌ SeverityIndex query failed: {e}")
        test_results['severity'] = 'FAILED'
    
    # Test 3: Job Name Index
    print("\n3️⃣  Testing JobNameIndex...")
    try:
        job_name = "WGMP110D"
        results = list(AbendDynamoTable.job_name_index.query(
            hash_key=job_name,
            limit=5
        ))
        print(f"   ✅ Found {len(results)} records for job '{job_name}'")
        test_results['job_name'] = len(results)
        
        if results:
            for record in results[:2]:  # Show first 2
                print(f"      - {record.tracking_id} | {record.adr_status}")
                
    except Exception as e:
        print(f"   ❌ JobNameIndex query failed: {e}")
        test_results['job_name'] = 'FAILED'
    
    # Test 4: Domain Area Index
    print("\n4️⃣  Testing DomainAreaIndex...")
    try:
        domain = "Claims Processing"
        results = list(AbendDynamoTable.domain_area_index.query(
            hash_key=domain,
            limit=5
        ))
        print(f"   ✅ Found {len(results)} records for domain '{domain}'")
        test_results['domain_area'] = len(results)
        
        if results:
            for record in results[:2]:  # Show first 2
                print(f"      - {record.tracking_id} | {record.job_name}")
                
    except Exception as e:
        print(f"   ❌ DomainAreaIndex query failed: {e}")
        test_results['domain_area'] = 'FAILED'
    
    # Test 5: Abend Type Index
    print("\n5️⃣  Testing AbendTypeIndex...")
    try:
        abend_type = "EFX"
        results = list(AbendDynamoTable.abend_type_index.query(
            hash_key=abend_type,
            limit=5
        ))
        print(f"   ✅ Found {len(results)} records for type '{abend_type}'")
        test_results['abend_type'] = len(results)
        
        if results:
            for record in results[:2]:  # Show first 2
                print(f"      - {record.tracking_id} | {record.job_name}")
                
    except Exception as e:
        print(f"   ❌ AbendTypeIndex query failed: {e}")
        test_results['abend_type'] = 'FAILED'
    
    return test_results


def test_range_key_queries():
    """Test range key queries on GSIs."""
    
    print("\n🕒 Testing Range Key Queries")
    print("=" * 40)
    
    try:
        from datetime import datetime, timezone
        
        # Test querying by date range
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        print(f"\n📅 Testing date-based queries for {today}...")
        
        # Query high severity records from today
        try:
            results = list(AbendDynamoTable.severity_index.query(
                hash_key=SeverityEnum.HIGH.value,
                range_key_condition=AbendDynamoTable.abended_at.startswith(today)
            ))
            print(f"   ✅ Found {len(results)} high severity records from today")
            
            for record in results[:3]:
                abended_time = record.abended_at.strftime("%H:%M:%S")
                print(f"      - {record.job_name} at {abended_time}")
                
        except Exception as e:
            print(f"   ❌ Range key query failed: {e}")
            
    except Exception as e:
        print(f"❌ Error in range key tests: {e}")


def diagnose_gsi_issues():
    """Diagnose potential GSI issues."""
    
    print("\n🔧 Diagnosing GSI Issues")
    print("=" * 40)
    
    # Check if records have the required GSI attributes
    print("\n📋 Checking sample records for GSI attributes...")
    
    try:
        # Get a few records and check their attributes
        records = list(AbendDynamoTable.scan(limit=3))
        
        for i, record in enumerate(records, 1):
            print(f"\n   Record {i}: {record.tracking_id}")
            
            # Check GSI hash key attributes
            gsi_attrs = {
                'adr_status': getattr(record, 'adr_status', None),
                'severity': getattr(record, 'severity', None),
                'job_name': getattr(record, 'job_name', None),
                'domain_area': getattr(record, 'domain_area', None),
                'abend_type': getattr(record, 'abend_type', None),
            }
            
            for attr_name, attr_value in gsi_attrs.items():
                status = "✅" if attr_value else "❌"
                print(f"      {status} {attr_name}: {attr_value}")
            
            # Check range key (abended_at)
            abended_at = getattr(record, 'abended_at', None)
            if abended_at:
                iso_string = AbendDynamoTable.datetime_to_iso_string(abended_at)
                print(f"      ✅ abended_at: {abended_at} → {iso_string}")
            else:
                print(f"      ❌ abended_at: Missing")
                
    except Exception as e:
        print(f"❌ Error checking records: {e}")


def main():
    """Main function to verify GSI status and functionality."""
    
    print("🔍 DynamoDB GSI Verification Tool")
    print("=" * 60)
    print("This tool checks the status and functionality of Global Secondary Indexes.\n")
    
    # Step 1: Check table and GSI status
    if not check_table_and_gsi_status():
        print("\n❌ Failed to check table status. Exiting.")
        return
    
    # Step 2: Test GSI queries
    test_results = test_gsi_queries()
    
    # Step 3: Test range key queries
    test_range_key_queries()
    
    # Step 4: Diagnose issues
    diagnose_gsi_issues()
    
    # Summary
    print(f"\n📊 Test Summary")
    print("=" * 30)
    
    working_gsis = 0
    total_gsis = len(test_results)
    
    for gsi_name, result in test_results.items():
        if result == 'FAILED':
            print(f"❌ {gsi_name}: FAILED")
        else:
            print(f"✅ {gsi_name}: {result} records")
            working_gsis += 1
    
    print(f"\n🎯 Result: {working_gsis}/{total_gsis} GSIs working correctly")
    
    if working_gsis == total_gsis:
        print("🎉 All GSIs are working correctly!")
    else:
        print("\n💡 If GSIs are failing:")
        print("1. Check if table was created with GSIs")
        print("2. Verify GSI status is ACTIVE")
        print("3. Wait for GSI backfill to complete")
        print("4. Check if records have required attributes")
        print("5. Verify DynamoDB permissions")


if __name__ == "__main__":
    main()
