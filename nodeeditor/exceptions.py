# -*- coding: utf-8 -*-
"""
Custom exception classes for the NodeEditor library.

This module defines all custom exceptions used throughout the NodeEditor framework,
providing clear error types for different failure scenarios.

Example:
    .. code-block:: python

        from nodeeditor.exceptions import NodeCreationError

        try:
            node = scene.create_node(NodeType)
        except NodeCreationError as e:
            print(f"Failed to create node: {e}")
"""


class NodeEditorException(Exception):
    """Base exception class for all NodeEditor-related errors."""
    pass


# ======================== Node-related exceptions ========================

class NodeError(NodeEditorException):
    """Base exception for node-related errors."""
    pass


class NodeCreationError(NodeError):
    """
    Raised when a node cannot be created.
    
    Example:
        Node initialization failed due to invalid parameters or missing scene reference.
    """
    pass


class NodeDeletionError(NodeError):
    """
    Raised when a node cannot be deleted.
    
    Example:
        Attempting to delete a node that is not in the scene.
    """
    pass


class NodeRegistrationError(NodeError):
    """
    Raised when a node type cannot be registered.
    
    Example:
        Attempting to register a node type that is already registered.
    """
    pass


class NodePropertyError(NodeError):
    """
    Raised when setting an invalid node property.
    
    Example:
        Attempting to set a property with an invalid value or type.
    """
    pass


# ======================== Socket/Port-related exceptions ========================

class SocketError(NodeEditorException):
    """Base exception for socket/port-related errors."""
    pass


class SocketConnectionError(SocketError):
    """
    Raised when sockets cannot be connected.
    
    Example:
        Attempting to connect two incompatible socket types.
    """
    pass


class SocketDisconnectionError(SocketError):
    """
    Raised when sockets cannot be disconnected.
    
    Example:
        Attempting to disconnect sockets that are not connected.
    """
    pass


class SocketRegistrationError(SocketError):
    """
    Raised when a socket cannot be registered with a node.
    
    Example:
        Attempting to add a socket to a node when one with the same name exists.
    """
    pass


# ======================== Edge-related exceptions ========================

class EdgeError(NodeEditorException):
    """Base exception for edge-related errors."""
    pass


class EdgeCreationError(EdgeError):
    """
    Raised when an edge cannot be created.
    
    Example:
        Attempting to create an edge between incompatible or invalid sockets.
    """
    pass


class EdgeValidationError(EdgeError):
    """
    Raised when edge validation fails.
    
    Example:
        A custom edge validator rejects the connection.
    """
    pass

class EdgeDeletionError(EdgeError):
    """
    Raised when edge deletion fails.

    Example:
        trying to delete the edge with wrong edge id.
    """


# ======================== Scene-related exceptions ========================

class SceneError(NodeEditorException):
    """Base exception for scene-related errors."""
    pass


class SceneSerializationError(SceneError):
    """
    Raised when scene serialization/deserialization fails.
    
    Example:
        JSON parsing error or missing required data in saved file.
    """
    pass


class SceneDeserializationError(SceneError):
    """
    Raised when scene deserialization fails.
    
    Example:
        Invalid file format or corrupted scene data.
    """
    pass


# ======================== History/Undo-Redo exceptions ========================

class HistoryError(NodeEditorException):
    """Base exception for history/undo-redo related errors."""
    pass


class HistoryStackError(HistoryError):
    """
    Raised when history stack operation fails.
    
    Example:
        Attempting to undo when history is empty.
    """
    pass


# ======================== Clipboard exceptions ========================

class ClipboardError(NodeEditorException):
    """Base exception for clipboard-related errors."""
    pass


class ClipboardSerializationError(ClipboardError):
    """
    Raised when clipboard data cannot be serialized.
    
    Example:
        Node data cannot be converted to clipboard format.
    """
    pass


class ClipboardDeserializationError(ClipboardError):
    """
    Raised when clipboard data cannot be deserialized.
    
    Example:
        Invalid clipboard format or corrupted data.
    """
    pass


# ======================== Serialization exceptions ========================

class SerializationError(NodeEditorException):
    """
    Raised when object serialization fails.
    
    Example:
        Node cannot be converted to dictionary format.
    """
    pass


class DeserializationError(NodeEditorException):
    """
    Raised when object deserialization fails.
    
    Example:
        Node cannot be created from dictionary data.
    """
    pass


# ======================== Factory exceptions ========================

class FactoryError(NodeEditorException):
    """Base exception for factory-related errors."""
    pass


class FactoryCreationError(FactoryError):
    """
    Raised when factory cannot create an object.
    
    Example:
        Node type not registered in factory.
    """
    pass


# ======================== Widget/UI exceptions ========================

class WidgetError(NodeEditorException):
    """Base exception for widget/UI-related errors."""
    pass


class ContentWidgetError(WidgetError):
    """
    Raised when node content widget operation fails.
    
    Example:
        Widget type not found or cannot be instantiated.
    """
    pass


# ======================== Validation exceptions ========================

class ValidationError(NodeEditorException):
    """
    Raised when data validation fails.
    
    Example:
        Invalid data format or constraint violation.
    """
    pass


# ======================== Configuration exceptions ========================

class ConfigurationError(NodeEditorException):
    """
    Raised when configuration is invalid.
    
    Example:
        Missing required configuration or invalid setting value.
    """
    pass
