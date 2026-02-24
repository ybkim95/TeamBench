"""Pytest fixtures for calculator tests."""
import pytest
from calculator.engine import Calculator


@pytest.fixture
def calc():
    """Fresh calculator instance for each test."""
    return Calculator()
