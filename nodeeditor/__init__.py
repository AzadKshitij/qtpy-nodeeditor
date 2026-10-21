# -*- coding: utf-8 -*-

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _dist_version

__name__ = 'Node Editor'
__author__ = 'Azad Kshitij'

try:
    __version__ = _dist_version("nodeeditor-qtpy")
except PackageNotFoundError:  # running from a source checkout
    __version__ = "0.8.1"


_QT_API_NAME, _QT_API_VERSION = None, None

if _QT_API_NAME is None:
    try:
        from PyQt5.QtCore import PYQT_VERSION_STR  # type: ignore
        _QT_API_NAME, _QT_API_VERSION = "pyqt5", PYQT_VERSION_STR
    except ImportError:
        pass

if _QT_API_NAME is None:
    try:
        from PySide2 import __version__  # type: ignore
        _QT_API_NAME, _QT_API_VERSION = "pyside2", __version__
    except ImportError:
        pass

if _QT_API_NAME is None:
    try:
        from PyQt6.QtCore import PYQT_VERSION_STR
        _QT_API_NAME, _QT_API_VERSION = "pyqt6", PYQT_VERSION_STR
    except ImportError:
        pass

if _QT_API_NAME is None:
    try:
        from PySide6 import __version__  # type: ignore
        _QT_API_NAME, _QT_API_VERSION = "pyside6", __version__
    except ImportError:
        pass

if _QT_API_NAME is None:
    raise ImportError(
        "No Qt binding found. Install nodeeditor-qtpy with one, e.g. "
        "'pip install nodeeditor-qtpy[pyqt6]' or "
        "'pip install nodeeditor-qtpy[pyside6]', "
        "or install PyQt5/PySide2/PyQt6/PySide6 directly."
    )

# Export color configuration classes for easier access
from nodeeditor.node_colors_config import (
    NodeEditorColorScheme,
    EdgeColors,
    SocketColors,
    get_color_scheme,
)

# Export the socket shape system for easier access
from nodeeditor.node_socket_shapes import (
    SocketShape,
    SocketShapeContext,
    CircleShape,
    SquareShape,
    TriangleShape,
    ChevronShape,
    register_socket_shape,
    get_socket_shape,
    SOCKET_SHAPES,
)

# Export the graph algorithm exception
from nodeeditor.node_graph import GraphCycleError


__all__ = [
    "NodeEditorColorScheme",
    "EdgeColors",
    "SocketColors",
    "get_color_scheme",
    "SocketShape",
    "SocketShapeContext",
    "CircleShape",
    "SquareShape",
    "TriangleShape",
    "ChevronShape",
    "register_socket_shape",
    "get_socket_shape",
    "SOCKET_SHAPES",
    "GraphCycleError",
]
