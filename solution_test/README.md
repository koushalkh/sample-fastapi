# ABEND System End-to-End Test Suite

This directory contains comprehensive end-to-end tests for the ABEND system, testing the complete workflow from API endpoints through to database operations.

## 🎯 Test Coverage

The test suite validates:

### Core ABEND Functionality
- ✅ ABEND creation via Internal API
- ✅ ABEND listing via UI API with pagination
- ✅ ABEND details retrieval
- ✅ Filtering by job name, domain area, severity
- ✅ Pagination with cursors

### Audit System Integration
- ✅ Audit log creation for ABEND records
- ✅ Audit log retrieval with pagination
- ✅ Audit trail completeness validation

### API Validation
- ✅ Health and readiness checks
- ✅ Request/response format validation
- ✅ Error handling for invalid requests
- ✅ HTTP status code validation

### Data Integrity
- ✅ Field mapping (camelCase ↔ snake_case)
- ✅ Datetime format validation
- ✅ ID generation validation (ULID format)
- ✅ Pagination metadata validation

## 🚀 Running the Tests

### Option 1: Direct Python Execution
```bash
# Run all tests with detailed output
python solution_test/run_tests.py
```

### Option 2: Using pytest
```bash
# Run with pytest (more detailed test reporting)
pytest solution_test/test_abend_e2e.py -v

# Run with coverage reporting
pytest solution_test/test_abend_e2e.py -v --cov=app

# Run specific test methods
pytest solution_test/test_abend_e2e.py::TestABENDEndToEnd::test_abend_creation_flow -v
```

### Option 3: From project root
```bash
# Make sure you're in the project root directory
cd /projects/ElevanceHealth/POTF/BAM/sample

# Run the test runner
python solution_test/run_tests.py
```

## 📋 Prerequisites

Before running the tests, ensure:

1. **FastAPI Server Dependencies**: All required packages are installed
2. **DynamoDB Tables**: ABEND tables are created (run `examples/create_table.py`)
3. **Environment Setup**: Local DynamoDB or AWS credentials configured

## 🧪 Test Structure

### `test_client.py`
- `ABENDTestClient`: Test client wrapper with convenience methods
- Helper functions for response validation
- Pytest fixtures and utilities

### `test_abend_e2e.py`
- `TestABENDEndToEnd`: Main test class with all test methods
- Individual test methods for each functionality area
- `run_all_tests()`: Standalone test runner function

### `run_tests.py`
- Command-line test runner script
- Handles test execution and result reporting
- Provides clear pass/fail status

### `conftest.py`
- Pytest configuration and fixtures
- Test environment setup

## 📊 Expected Test Output

When tests pass, you'll see output like:

```
🚀 Starting ABEND End-to-End Tests
==================================================

🧪 Running: test_health_and_readiness_checks
✅ PASSED: test_health_and_readiness_checks

🧪 Running: test_abend_creation_flow
🏗️  Testing ABEND Creation
✅ ABEND created successfully: ABEND_E2E_TEST_JOB_01K1XYZ...
✅ PASSED: test_abend_creation_flow

🧪 Running: test_audit_log_functionality
📝 Testing Audit Log Functionality
✅ Audit log created: AUDIT_01K1XYZ... for action: STATUS_CHANGE
✅ Retrieved 3 audit logs successfully
✅ PASSED: test_audit_log_functionality

🎯 Test Results: 7/7 tests passed
🎉 All tests passed! ABEND system is working correctly.
```

## 🔧 Test Configuration

### Environment Variables
The tests use the same environment configuration as the main application:
- `ADR_ENV`: Environment setting (defaults to "Local")
- `API_MODE`: API mode for route initialization (defaults to "ALL")

### Test Data Management
- Tests create temporary ABEND records for validation
- Test data is tracked and can be cleaned up automatically
- No permanent test data is left in the database

## 🎯 Test Scenarios

### Scenario 1: Basic ABEND Flow
1. Create ABEND via Internal API
2. Verify creation response format
3. Retrieve ABEND via UI API
4. Validate data consistency

### Scenario 2: Audit Integration
1. Create ABEND record
2. Add multiple audit log entries
3. Retrieve audit logs
4. Verify complete audit trail

### Scenario 3: Filtering & Pagination
1. Create multiple ABEND records
2. Test filtering by various criteria
3. Test pagination with different limits
4. Validate metadata accuracy

### Scenario 4: Error Handling
1. Test invalid ABEND creation
2. Test non-existent record retrieval
3. Validate error response formats
4. Check appropriate HTTP status codes

### Scenario 5: Complete Lifecycle
1. Create ABEND
2. Verify in listings
3. Get detailed information
4. Create complete audit trail
5. Validate end-to-end data flow

## 🚨 Troubleshooting

### Common Issues

**Server Not Running**
```bash
# Start the FastAPI server first
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Missing Dependencies**
```bash
# Install test dependencies
pip install pytest pytest-cov fastapi[all]
```

**Database Not Ready**
```bash
# Create tables first
python examples/create_table.py
```

**Import Errors**
```bash
# Run from project root directory
cd /projects/ElevanceHealth/POTF/BAM/sample
python solution_test/run_tests.py
```

## 📈 Extending the Tests

To add new test scenarios:

1. Add methods to `TestABENDEndToEnd` class
2. Follow the naming convention: `test_<functionality>`
3. Use the provided helper functions for validation
4. Update the test list in `run_all_tests()` function

Example:
```python
def test_new_functionality(self):
    """Test new ABEND functionality."""
    client = ABENDTestClient()
    
    # Your test logic here
    response = client.some_new_method()
    assert_response_success(response)
    
    print("✅ New functionality test passed")
```

## 🎉 Success Criteria

All tests pass when:
- ✅ All HTTP responses have correct status codes
- ✅ All response data contains required fields
- ✅ All datetime formats are valid ISO 8601
- ✅ All ID formats follow expected patterns
- ✅ Pagination metadata is accurate
- ✅ Filtering works correctly
- ✅ Audit logs are created and retrievable
- ✅ Error handling works as expected

The test suite validates that the ABEND system is production-ready and all components work together seamlessly.
