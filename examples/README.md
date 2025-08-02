# ABEND Database Usage Guide

This directory contains examples and documentation for using the ABEND (Abnormal End) database schema and models.

## Files

- `abend_db_usage.py` - Comprehensive usage examples with code demonstrations
- `abend_schema_examples.py` - Schema structure examples and data patterns
- `README.md` - This guide

## Quick Start

### 1. Creating a New ABEND Record

```python
from app.schema.abend_dynamo import AbendDynamoTable
from app.models.abend import ADRStatusEnum, SeverityEnum
from datetime import datetime, timezone

# Generate tracking ID
tracking_id = AbendDynamoTable.generate_tracking_id("WGMP110D")

# Create record
abend_record = AbendDynamoTable(
    tracking_id=tracking_id,
    abended_at=datetime.now(timezone.utc),
    job_id="IYM98ID",
    job_name="WGMP110D",
    adr_status=ADRStatusEnum.ABEND_REGISTERED.value,
    severity=SeverityEnum.HIGH.value,
    domain_area="Claims Processing"
)

# Save to DynamoDB
abend_record.save()
```

### 2. Querying Records

```python
# Query by ADR status (current day)
today_iso = AbendDynamoTable.datetime_to_iso_string(datetime.now(timezone.utc))
results = AbendDynamoTable.adr_status_index.query(
    hash_key=ADRStatusEnum.PENDING_MANUAL_APPROVAL.value,
    range_key_condition=AbendDynamoTable.abended_at.startswith(today_iso[:10])
)

# Query by severity
high_severity_records = AbendDynamoTable.severity_index.query(
    hash_key=SeverityEnum.HIGH.value
)
```

### 3. Updating Status

```python
# Retrieve existing record
record = AbendDynamoTable.get(tracking_id, abended_at)

# Update status
record.adr_status = ADRStatusEnum.AI_ANALYSIS_INITIATED.value
record.updated_by = "ai_service"

# Save changes (auto-updates updated_at)
record.save()
```

## ADR Status Workflow

The system follows this status progression:

1. **ABEND_REGISTERED** - Initial state when abend notification received
2. **LOG_EXTRACTION_INITIATED** - Log extraction process started
3. **MANUAL_INTERVENTION_REQUIRED** - Manual intervention needed (error state)
4. **LOG_UPLOAD_TO_S3** - Log uploaded to S3
5. **PREPROCESSING_LOG_FILE** - Log file being preprocessed
6. **AI_ANALYSIS_INITIATED** - AI analysis triggered
7. **MANUAL_ANALYSIS_REQUIRED** - Manual analysis required (AI failed)
8. **REMEDIATION_SUGGESTIONS_GENERATED** - AI suggestions generated
9. **AUTOMATED_REMEDIATION_IN_PROGRESS** - Auto remediation executing
10. **PENDING_MANUAL_APPROVAL** - Waiting for manual approval
11. **VERIFICATION_IN_PROGRESS** - Verifying remediation results
12. **RESOLVED** - Final resolved state

## Schema Structure

### Primary Key
- **tracking_id** (Hash Key): Format `ABEND_{jobname}_{ulid}`
- **abended_at** (Range Key): UTC datetime when abend occurred

### Global Secondary Indexes
- **ADRStatusIndex**: Query by `adr_status` + `abended_at`
- **SeverityIndex**: Query by `severity` + `abended_at`
- **JobNameIndex**: Query by `job_name` + `abended_at`
- **DomainAreaIndex**: Query by `domain_area` + `abended_at`
- **AbendTypeIndex**: Query by `abend_type` + `abended_at`

### Key Fields

#### Basic Information
- `job_id`, `job_name`, `order_id`, `incident_number`
- `fa_id`, `domain_area`

#### ABEND Details
- `abend_type`, `abend_step`, `abend_return_code`, `abend_reason`

#### Status & Priority
- `adr_status` (ADRStatusEnum)
- `severity` (SeverityEnum: High, Medium, Low)

#### Performance Metrics (Flattened)
- `perf_log_extraction_time`, `perf_ai_analysis_time`
- `perf_remediation_time`, `perf_total_automated_time`

#### Log Extraction (Flattened)
- `log_extraction_run_id`, `log_extraction_retries`

#### Complex Objects (JSON)
- `email_metadata`: Email notification details
- `knowledge_base_metadata`: SOP and file references
- `remediation_metadata`: AI recommendations and approvals

#### Audit Fields
- `created_at`, `updated_at`, `created_by`, `updated_by`, `generation`

## Best Practices

### 1. Datetime Handling
- Always use UTC datetime
- Use helper methods for GSI queries:
  ```python
  iso_string = AbendDynamoTable.datetime_to_iso_string(datetime_obj)
  datetime_obj = AbendDynamoTable.iso_string_to_datetime(iso_string)
  ```

### 2. Tracking ID Generation
```python
tracking_id = AbendDynamoTable.generate_tracking_id(job_name)
# Result: "ABEND_WGMP110D_01ARZ3NDEKTSV4RRFFQ69G5FAV" (auto-generated ULID)
```

### 3. JSON Field Updates
```python
# Use helper methods for complex objects
abend_record.set_email_metadata(email_dict)
abend_record.set_knowledge_base_metadata(kb_dict)
abend_record.set_remediation_metadata(remediation_dict)
```

### 4. Pydantic Validation
```python
from app.models.abend import AbendModel, AbendDetailsModel

# For API validation
basic_abend = AbendModel(**api_payload)
detailed_abend = AbendDetailsModel(**full_payload)
```

### 5. Querying Current Day Records
```python
today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
results = AbendDynamoTable.adr_status_index.query(
    hash_key=status,
    range_key_condition=AbendDynamoTable.abended_at.startswith(today)
)
```

## Error Handling

Always wrap database operations in try-catch blocks:

```python
try:
    abend_record.save()
except Exception as e:
    logger.error(f"Failed to save ABEND record: {e}")
    # Handle error appropriately
```

## Running Examples

```bash
# From the examples directory
python abend_db_usage.py
python abend_schema_examples.py
```

## Notes

- The schema supports both basic table views (`AbendModel`) and detailed views (`AbendDetailsModel`)
- All datetime fields are stored as UTC
- GSI queries use ISO 8601 string format for range keys
- Complex nested objects are stored as JSON in DynamoDB
- Generation field tracks record updates
- The system is designed for high-frequency current-day queries
