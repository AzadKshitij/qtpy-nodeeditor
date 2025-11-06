"""
Content Widgets - Custom Widgets for Node Content Display

This module contains custom widgets that can be embedded in nodes for displaying
content, editing properties, and other interactive elements.
"""

from .node_content_widget import QDMNodeContentWidget
from .node_icon_content_widget import QDMNodeIconContentWidget

__all__ = [
    "QDMNodeContentWidget",
    "QDMNodeIconContentWidget",
]
