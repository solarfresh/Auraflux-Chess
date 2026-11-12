from unittest.mock import MagicMock

import pytest
from canvases.models import Canvas, Edge, Node

# -------------------------------------------------------------------------
# Global Environment & Third-Party Mocks
# -------------------------------------------------------------------------

def pytest_configure(config):
    """
    Hook into pytest configuration to modify Django settings dynamically before setup.
    This safely bypasses the 'logfile' handler directory dependency during tests.
    """
    from django.conf import settings

    # Check if Django settings are configured and LOGGING dict exists
    if hasattr(settings, "LOGGING") and "handlers" in settings.LOGGING:
        if "logfile" in settings.LOGGING["handlers"]:
            # Dynamically switch the file handler to a safe console output or NullHandler
            settings.LOGGING["handlers"]["logfile"] = {
                "class": "logging.StreamHandler",  # Redirect to stdout/stderr
                "formatter": "verbose" if "verbose" in settings.LOGGING.get("formatters", {}) else None
            }

# -------------------------------------------------------------------------
# API Client Fixtures (For Integration Endpoint Testing)
# -------------------------------------------------------------------------

@pytest.fixture
def authenticated_api_client(test_user):
    """
    Provides an adrf / rest_framework API Client injected with pre-verified
    credentials acting as the logged-in target user context.
    """
    from rest_framework.test import APIClient
    client = APIClient()
    client.force_authenticate(user=test_user)
    return client


@pytest.fixture
def mock_semaphore():
    return MagicMock()

@pytest.fixture
def canvas(db):
    canvas = Canvas.objects.create(title="Test Canvas")
    return canvas


class MockModelManager:
    def __init__(self, instance=None, raise_does_not_exist=False):
        self.instance = instance
        self.raise_does_not_exist = raise_does_not_exist

    def get(self, **kwargs):
        if self.raise_does_not_exist:
            raise Exception("Not found")
        return self.instance


class MockModel:
    class DoesNotExist(Exception):
        pass


@pytest.fixture
def mock_model_manager_factory():
    def _factory(instance=None, raise_does_not_exist=False):
        return MockModelManager(instance=instance, raise_does_not_exist=raise_does_not_exist)
    return _factory


@pytest.fixture
def mock_model_instance():
    instance = MagicMock()
    instance.pk = 1
    return instance
