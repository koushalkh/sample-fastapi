"""
pytest configuration for solution_test

Provides pytest fixtures and configuration for end-to-end testing.
"""

import pytest
import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


@pytest.fixture(scope="session")
def test_app():
    """Fixture to provide the FastAPI app for testing."""
    from app.main import app
    return app


@pytest.fixture(scope="function")
def abend_test_client():
    """Fixture to provide a clean ABEND test client for each test."""
    from solution_test.test_client import ABENDTestClient
    
    client = ABENDTestClient()
    yield client
    # Cleanup after test
    client.cleanup_test_data()


# Configure pytest
def pytest_configure(config):
    """Configure pytest for end-to-end testing."""
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end tests"
    )
    config.addinivalue_line(
        "markers", "abend: marks tests as ABEND-related tests"
    )
    config.addinivalue_line(
        "markers", "audit: marks tests as audit-related tests"
    )
