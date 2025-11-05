# -*- coding: utf-8 -*-

__author__ = 'Azad Kshitij'
__version__ = "0.1.8"


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

# don't be too strict yet...
# if _QT_API_NAME is None:
#     raise ImportError("Please install PyQt5/PySide2 or PyQt6/PySide6")

# Import industry-standard modules for better architecture
from nodeeditor.exceptions import (
    NodeEditorException,
    NodeError,
    NodeCreationError,
    NodeDeletionError,
    NodeRegistrationError,
    NodePropertyError,
    SocketError,
    SocketConnectionError,
    SocketDisconnectionError,
    EdgeError,
    EdgeCreationError,
    EdgeValidationError,
    SceneError,
    SceneSerializationError,
    SerializationError,
    ValidationError,
)

from nodeeditor.constants import (
    NodeZValue,
    SocketType,
    EdgeType,
    LayoutDirection,
    NodeColors,
    TimingSettings,
    SerializationKeys,
)

from nodeeditor.commands import (
    BaseCommand,
    NodeCreatedCmd,
    NodeDeletedCmd,
    NodeMovedCmd,
    NodeRenamedCmd,
    EdgeCreatedCmd,
    EdgeDeletedCmd,
    NodesMovedCmd,
    NodesDeletedCmd,
)

# Import MVC Model Layer for robust architecture
from nodeeditor.models import (
    NodeModel,
    EdgeModel,
    SocketModel,
    SceneModel,
)

# Import MVC Controller Layer for business logic
from nodeeditor.controllers import (
    NodeController,
    EdgeController,
    SceneController,
)

# Import View Layer for graphics synchronization
from nodeeditor.view import (
    QDMGraphicsNodeModel,
    QDMGraphicsEdgeModel,
    QDMGraphicsSocketModel,
    QDMGraphicsSceneModel,
)

# Import Edge Validator Registration (auto-registers validators)
from nodeeditor import edge_validator_registration  # noqa: F401


__all__ = [
    # Exceptions
    "NodeEditorException",
    "NodeError",
    "NodeCreationError",
    "NodeDeletionError",
    "NodeRegistrationError",
    "NodePropertyError",
    "SocketError",
    "SocketConnectionError",
    "SocketDisconnectionError",
    "EdgeError",
    "EdgeCreationError",
    "EdgeValidationError",
    "SceneError",
    "SceneSerializationError",
    "SerializationError",
    "ValidationError",
    # Constants
    "NodeZValue",
    "SocketType",
    "EdgeType",
    "LayoutDirection",
    "NodeColors",
    "TimingSettings",
    "SerializationKeys",
    # Commands (Undo/Redo)
    "BaseCommand",
    "NodeCreatedCmd",
    "NodeDeletedCmd",
    "NodeMovedCmd",
    "NodeRenamedCmd",
    "EdgeCreatedCmd",
    "EdgeDeletedCmd",
    "NodesMovedCmd",
    "NodesDeletedCmd",
    # Models (MVC Layer)
    "NodeModel",
    "EdgeModel",
    "SocketModel",
    "SceneModel",
    # Controllers (Business Logic Layer)
    "NodeController",
    "EdgeController",
    "SceneController",
    # View Layer (Graphics Integration)
    "QDMGraphicsNodeModel",
    "QDMGraphicsEdgeModel",
    "QDMGraphicsSocketModel",
    "QDMGraphicsSceneModel",
]
