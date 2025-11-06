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

# Import exceptions
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

# Import constants
from nodeeditor.constants import (
    NodeZValue,
    SocketType,
    EdgeType,
    LayoutDirection,
    NodeColors,
    TimingSettings,
    SerializationKeys,
)

# Import commands (undo/redo)
from nodeeditor.commands import (
    BaseCommand,
    NodeCreatedCmd,
    NodeDeletedCmd,
    NodeMovedCmd,
    NodeRenamedCmd,
    NodePropertyChangedCmd,
    EdgeCreatedCmd,
    EdgeDeletedCmd,
    NodesMovedCmd,
    NodesDeletedCmd,
    SceneClearedCmd,
)

# Import models (MVC Model Layer)
from nodeeditor.models import (
    NodeModel,
    NodeIconModel,
    EdgeModel,
    SocketModel,
    SceneModel,
    GroupNodeModel,
    EdgeDraggingModel,
)

# Import controllers (Business Logic Layer)
from nodeeditor.controllers import (
    NodeController,
    EdgeController,
    SceneController,
    GroupNodeController,
)

# Import utility functions (from utils package __init__ which re-exports everything)
from nodeeditor.utils import (
    qpointf_to_tuple,
    tuple_to_qpointf,
    qsizef_to_tuple,
    tuple_to_qsizef,
    qrectf_to_dict,
    dict_to_qrectf,
    qcolor_to_hex,
    hex_to_qcolor,
    normalize_point,
    normalize_size,
    normalize_rect,
    floats_equal,
    tuples_equal,
    qpointf_equal,
    qsizef_equal,
    qrectf_equal,
    qcolor_equal,
    dict_equal,
    dicts_contain_equal_values,
    any_values_equal,
    DEFAULT_FLOAT_TOLERANCE,
    edge_validator_debug,
    edge_cannot_connect_two_outputs_or_two_inputs,
    edge_cannot_connect_input_and_output_of_same_node,
    edge_cannot_connect_input_and_output_of_different_type,
    loadStylesheet,
    loadStylesheets,
    isCTRLPressed,
    isSHIFTPressed,
    isALTPressed,
)

# Import graphics/views (MVC View Layer)
from nodeeditor.views import (
    QDMGraphicsEdge,
    GraphicsEdgePathBezier,
    GraphicsEdgePathDirect,
    GraphicsEdgePathSquare,
    GraphicsEdgePathImprovedSharp,
    GraphicsEdgePathImprovedBezier,
    QDMGraphicsNode,
    QDMGraphicsSocket,
    QDMGraphicsView,
    QDMGraphicsScene,
    QDMCutLine,
    QDMGraphicsGroupNode,
    NodeEditorWindow,
    QDMNodeContentWidget,
    QDMNodeIconContentWidget,
    IconRegistry,
    get_icon_registry,
    set_icon_registry,
)

# Import legacy view layer models
from nodeeditor.view import (
    QDMGraphicsNodeModel,
    QDMGraphicsEdgeModel,
    QDMGraphicsSocketModel,
    QDMGraphicsSceneModel,
)

# Import Edge Validator Registration
from nodeeditor import edge_validator_registration  # noqa: F401


__all__ = [
    "__version__",
    "__author__",
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
    "NodeZValue",
    "SocketType",
    "EdgeType",
    "LayoutDirection",
    "NodeColors",
    "TimingSettings",
    "SerializationKeys",
    "BaseCommand",
    "NodeCreatedCmd",
    "NodeDeletedCmd",
    "NodeMovedCmd",
    "NodeRenamedCmd",
    "NodePropertyChangedCmd",
    "EdgeCreatedCmd",
    "EdgeDeletedCmd",
    "NodesMovedCmd",
    "NodesDeletedCmd",
    "SceneClearedCmd",
    "NodeModel",
    "NodeIconModel",
    "EdgeModel",
    "SocketModel",
    "SceneModel",
    "GroupNodeModel",
    "EdgeDraggingModel",
    "NodeController",
    "EdgeController",
    "SceneController",
    "GroupNodeController",
    "qpointf_to_tuple",
    "tuple_to_qpointf",
    "qsizef_to_tuple",
    "tuple_to_qsizef",
    "qrectf_to_dict",
    "dict_to_qrectf",
    "qcolor_to_hex",
    "hex_to_qcolor",
    "normalize_point",
    "normalize_size",
    "normalize_rect",
    "floats_equal",
    "tuples_equal",
    "qpointf_equal",
    "qsizef_equal",
    "qrectf_equal",
    "qcolor_equal",
    "dict_equal",
    "dicts_contain_equal_values",
    "any_values_equal",
    "DEFAULT_FLOAT_TOLERANCE",
    "edge_validator_debug",
    "edge_cannot_connect_two_outputs_or_two_inputs",
    "edge_cannot_connect_input_and_output_of_same_node",
    "edge_cannot_connect_input_and_output_of_different_type",
    "loadStylesheet",
    "loadStylesheets",
    "isCTRLPressed",
    "isSHIFTPressed",
    "isALTPressed",
    "QDMGraphicsEdge",
    "GraphicsEdgePathBezier",
    "GraphicsEdgePathDirect",
    "GraphicsEdgePathSquare",
    "GraphicsEdgePathImprovedSharp",
    "GraphicsEdgePathImprovedBezier",
    "QDMGraphicsNode",
    "QDMGraphicsSocket",
    "QDMGraphicsView",
    "QDMGraphicsScene",
    "QDMCutLine",
    "QDMGraphicsGroupNode",
    "NodeEditorWindow",
    "QDMNodeContentWidget",
    "QDMNodeIconContentWidget",
    "IconRegistry",
    "get_icon_registry",
    "set_icon_registry",
    "QDMGraphicsNodeModel",
    "QDMGraphicsEdgeModel",
    "QDMGraphicsSocketModel",
    "QDMGraphicsSceneModel",
]
