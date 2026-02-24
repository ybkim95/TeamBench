"""Test fixtures using requests_mock."""
import pytest

try:
    import requests_mock as rm
    @pytest.fixture
    def mock_api():
        with rm.Mocker() as m:
            yield m
except ImportError:
    pass
