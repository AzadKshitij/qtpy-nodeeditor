"""
Pytest configuration file for pytest-qt integration.

This file provides fixtures and configuration for Qt-based testing using pytest-qt.
"""

import pytest
from qtpy.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp():
    """
    Create a QApplication instance for the entire test session.
    
    pytest-qt automatically handles this, but we can provide custom configuration here.
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def qtbot_config(qtbot):
    """
    Configure qtbot behavior for all tests.
    
    This fixture provides access to qtbot configuration options.
    """
    # Set a default timeout for signal waiting
    qtbot.wait_signal_timeout = 5000  # 5 seconds
    return qtbot


@pytest.fixture
def clear_validators():
    """
    Fixture to clear edge validators before/after tests.
    
    Use this fixture in tests that modify the EdgeModel validators.
    """
    from nodeeditor.models import EdgeModel
    
    # Clear before test
    EdgeModel.clear_edge_validators()
    
    yield
    
    # Clear after test
    EdgeModel.clear_edge_validators()
