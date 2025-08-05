"""
Test Configuration and Client Setup

This module provides the FastAPI TestClient setup and common test utilities
for end-to-end testing of the ABEND system.
"""

from fastapi.testclient import TestClient
from datetime import datetime, timezone
import json
from typing import Dict, Any, Optional
import pytest

from app.main import app


class ABENDTestClient:
    """
    Test client wrapper for ABEND API testing.
    
    Provides convenience methods for testing ABEND and audit functionality
    with proper setup and teardown.
    """
    
    def __init__(self):
        self.client = TestClient(app)
        self.base_url_ui = "/adr/ui/v1alpha1/abend"
        self.base_url_internal = "/adr/internal/v1alpha1/abend"
        self.created_tracking_ids = []  # Track created records for cleanup
    
    def create_abend(self, job_name: str = "E2E_TEST_JOB", custom_data: Optional[Dict[str, Any]] = None):
        """Create an ABEND record for testing."""
        from datetime import datetime, timezone
        
        data = {
            "abendedAt": datetime.now(timezone.utc).isoformat(),
            "jobName": job_name,
            "orderId": f"ORDER_{job_name}",
            "serviceNowGroup": "TEST_GROUP",
            "incidentId": f"INC{job_name[:10]}{datetime.now().strftime('%H%M%S')}",
            "severity": "MEDIUM"
        }
        
        if custom_data:
            data.update(custom_data)
        
        response = self.client.post(
            "/adr/internal/v1alpha1/abend/",
            json=data
        )
        return response
    
    def get_abends_ui(self, **query_params: Any):
        """
        Get ABEND records via UI API.
        
        Args:
            **query_params: Query parameters for filtering
            
        Returns:
            Response from UI API
        """
        return self.client.get(
            f"{self.base_url_ui}/",
            params=query_params
        )
    
    def get_abend_details_ui(self, tracking_id: str):
        """
        Get ABEND details via UI API.
        
        Args:
            tracking_id: ABEND tracking ID
            
        Returns:
            Response from UI API
        """
        return self.client.get(f"{self.base_url_ui}/{tracking_id}")
    
    def get_abends_internal(self, **query_params: Any):
        """
        Get ABEND records via internal API.
        
        Args:
            **query_params: Query parameters for filtering
            
        Returns:
            Response from internal API
        """
        return self.client.get(
            f"{self.base_url_internal}/",
            params=query_params
        )
    
    def create_audit_log(self, tracking_id: str, message: str = "Test audit message", level: str = "INFO"):
        """
        Create an audit log entry for testing.
        
        Args:
            tracking_id: ABEND tracking ID
            message: Audit message
            level: Audit level
            
        Returns:
            Response from internal API
        """
        audit_data = {
            "trackingID": tracking_id,  # Required field with correct name
            "level": level,
            "adrStatus": "ABEND_REGISTERED",
            "message": message,
            "description": f"Test audit log created for {tracking_id}",
            "createdBy": "test-user"
        }
        
        return self.client.post(
            f"{self.base_url_internal}/audit-logs",
            json=audit_data,
            headers={"Content-Type": "application/json"}
        )
    
    def get_audit_logs(self, tracking_id: str) -> Dict[str, Any]:
        """
        Get audit logs for an ABEND record.
        
        Args:
            tracking_id: ABEND tracking ID
            
        Returns:
            Response with audit logs
        """
        return self.client.get(f"{self.base_url_ui}/{tracking_id}/audit-logs")
    
    def get_health_check(self) -> Dict[str, Any]:
        """Get health check status."""
        return self.client.get("/healthz")
    
    def get_readiness_check(self) -> Dict[str, Any]:
        """Get readiness check status."""
        return self.client.get("/readyz")
    
    def cleanup_test_data(self):
        """
        Clean up any test data created during testing.
        
        Note: This is a placeholder - in real scenarios you might want
        to delete test records or mark them for cleanup.
        """
        print(f"Cleaning up {len(self.created_tracking_ids)} test ABEND records")
        # In a real scenario, you might call delete endpoints here
        self.created_tracking_ids.clear()


# Test fixtures and utilities
@pytest.fixture
def abend_client():
    """Pytest fixture for ABEND test client."""
    client = ABENDTestClient()
    yield client
    client.cleanup_test_data()


def assert_response_success(response, expected_status: int = 200):
    """
    Assert that a response is successful.
    
    Args:
        response: Response from TestClient
        expected_status: Expected HTTP status code
    """
    assert response.status_code == expected_status, f"Expected {expected_status}, got {response.status_code}. Response: {response.text}"


def assert_response_has_fields(response_data: Dict[str, Any], required_fields: list):
    """
    Assert that response data contains required fields.
    
    Args:
        response_data: Response JSON data
        required_fields: List of required field names
    """
    for field in required_fields:
        assert field in response_data, f"Required field '{field}' not found in response"


def assert_pagination_metadata(meta: Dict[str, Any]):
    """
    Assert that pagination metadata is properly formatted.
    
    Args:
        meta: Pagination metadata from response
    """
    required_fields = ["total", "limit", "hasNext", "hasPrevious"]
    for field in required_fields:
        assert field in meta, f"Pagination field '{field}' missing"
    
    assert isinstance(meta["total"], int), "total should be an integer"
    assert isinstance(meta["limit"], int), "limit should be an integer" 
    assert isinstance(meta["hasNext"], bool), "hasNext should be a boolean"
    assert isinstance(meta["hasPrevious"], bool), "hasPrevious should be a boolean"


def assert_datetime_format(datetime_str: str):
    """
    Assert that a datetime string is in the correct ISO format.
    
    Args:
        datetime_str: Datetime string to validate
    """
    try:
        # Parse ISO format datetime
        parsed_dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        assert parsed_dt.tzinfo is not None, "Datetime should include timezone info"
    except ValueError as e:
        pytest.fail(f"Invalid datetime format '{datetime_str}': {e}")


def print_test_response(response, description: str = "Response"):
    """
    Print response details for debugging.
    
    Args:
        response: Response from TestClient
        description: Description of the response
    """
    print(f"\n=== {description} ===")
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    
    try:
        response_data = response.json()
        print(f"Response Body: {json.dumps(response_data, indent=2)}")
    except:
        print(f"Response Text: {response.text}")
    print("=" * (len(description) + 8))
