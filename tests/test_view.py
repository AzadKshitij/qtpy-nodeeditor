"""
Unit tests for the View Layer (Phase 3).

Tests for graphics model wrappers and scene coordination including:
- Graphics node model synchronization
- Graphics edge model synchronization
- Graphics socket model synchronization
- Scene coordinator functionality

Note: These tests use MagicMock for graphics items to avoid Qt dependency issues.
Full integration tests with actual Qt objects are in integration tests.
"""

import pytest
from unittest.mock import Mock, MagicMock, call

# Import models
from nodeeditor.models import (
    NodeModel,
    EdgeModel,
    SocketModel,
    SceneModel,
)

# Import view layer
from nodeeditor.view import (
    QDMGraphicsNodeModel,
    QDMGraphicsEdgeModel,
    QDMGraphicsSocketModel,
    QDMGraphicsSceneModel,
)


# ======================== Fixtures ========================

@pytest.fixture
def node_model():
    """Create a test NodeModel."""
    return NodeModel("test_node", "TestNode")


@pytest.fixture
def edge_model():
    """Create a test EdgeModel."""
    return EdgeModel()


@pytest.fixture
def socket_model():
    """Create a test SocketModel."""
    return SocketModel("input", SocketModel.INPUT)


@pytest.fixture
def scene_model():
    """Create a test SceneModel."""
    return SceneModel()


@pytest.fixture
def mock_graphics_node():
    """Create a mock QDMGraphicsNode."""
    mock = MagicMock()
    mock.title = ""
    mock.pos.return_value = MagicMock(x=lambda: 0, y=lambda: 0)
    mock.setPos = MagicMock()
    mock.setSelected = MagicMock()
    mock.isSelected = MagicMock(return_value=False)
    mock.setVisible = MagicMock()
    return mock


@pytest.fixture
def mock_graphics_edge():
    """Create a mock QDMGraphicsEdge."""
    mock = MagicMock()
    mock.edge_type = 1
    mock.update_path = MagicMock()
    return mock


@pytest.fixture
def mock_graphics_socket():
    """Create a mock QDMGraphicsSocket."""
    mock = MagicMock()
    mock._color_background = None
    mock._brush = MagicMock()
    mock.changeSocketType = MagicMock()
    mock.update = MagicMock()
    return mock


@pytest.fixture
def mock_graphics_scene():
    """Create a mock QDMGraphicsScene."""
    return MagicMock()


# ======================== QDMGraphicsNodeModel Tests ========================

class TestQDMGraphicsNodeModel:
    """Test suite for QDMGraphicsNodeModel."""

    def test_initialization(self, node_model, mock_graphics_node):
        """Test graphics node model initialization."""
        wrapper = QDMGraphicsNodeModel(node_model, mock_graphics_node)
        assert wrapper.model is node_model
        assert wrapper.graphics_item is mock_graphics_node
        assert wrapper.controller is None

    def test_initialization_with_invalid_model(self, mock_graphics_node):
        """Test initialization fails with invalid model."""
        invalid_model = object()  # Not a NodeModel
        with pytest.raises((TypeError, AttributeError)):
            QDMGraphicsNodeModel(invalid_model, mock_graphics_node)  # type: ignore

    def test_node_id_property(self, node_model, mock_graphics_node):
        """Test node_id property."""
        wrapper = QDMGraphicsNodeModel(node_model, mock_graphics_node)
        assert wrapper.node_id == node_model.id

    def test_node_type_property(self, node_model, mock_graphics_node):
        """Test node_type property."""
        wrapper = QDMGraphicsNodeModel(node_model, mock_graphics_node)
        assert wrapper.node_type == "test_node"

    def test_set_title(self, node_model, mock_graphics_node):
        """Test setting node title."""
        wrapper = QDMGraphicsNodeModel(node_model, mock_graphics_node)
        wrapper.set_title("New Title")
        assert mock_graphics_node.title == "New Title"

    def test_title_changed_signal(self, node_model, mock_graphics_node):
        """Test title changed signal from model."""
        wrapper = QDMGraphicsNodeModel(node_model, mock_graphics_node)
        signal_received = []
        wrapper.graphicsUpdated.connect(lambda: signal_received.append(True))

        node_model.title = "Updated Title"
        assert len(signal_received) > 0

    def test_position_changed_signal(self, node_model, mock_graphics_node):
        """Test position changed signal from model."""
        wrapper = QDMGraphicsNodeModel(node_model, mock_graphics_node)
        signal_received = []
        wrapper.positionChanged.connect(lambda pos: signal_received.append(pos))

        node_model.position = (100, 200)
        assert len(signal_received) > 0

    def test_selected_changed_signal(self, node_model, mock_graphics_node):
        """Test selection changed signal from model."""
        wrapper = QDMGraphicsNodeModel(node_model, mock_graphics_node)
        signal_received = []
        wrapper.selectionChanged.connect(lambda sel: signal_received.append(sel))

        node_model.selected = True
        assert len(signal_received) > 0

    def test_set_visible(self, node_model, mock_graphics_node):
        """Test setting node visibility."""
        wrapper = QDMGraphicsNodeModel(node_model, mock_graphics_node)
        wrapper.set_visible(False)
        mock_graphics_node.setVisible.assert_called_with(False)


# ======================== QDMGraphicsEdgeModel Tests ========================

class TestQDMGraphicsEdgeModel:
    """Test suite for QDMGraphicsEdgeModel."""

    def test_initialization(self, edge_model, mock_graphics_edge):
        """Test graphics edge model initialization."""
        wrapper = QDMGraphicsEdgeModel(edge_model, mock_graphics_edge)
        assert wrapper.model is edge_model
        assert wrapper.graphics_item is mock_graphics_edge

    def test_initialization_with_invalid_model(self, mock_graphics_edge):
        """Test initialization fails with invalid model."""
        invalid_model = object()  # Not an EdgeModel
        with pytest.raises((TypeError, AttributeError)):
            QDMGraphicsEdgeModel(invalid_model, mock_graphics_edge)  # type: ignore

    def test_edge_id_property(self, edge_model, mock_graphics_edge):
        """Test edge_id property."""
        wrapper = QDMGraphicsEdgeModel(edge_model, mock_graphics_edge)
        assert wrapper.edge_id == edge_model.id

    def test_set_type(self, edge_model, mock_graphics_edge):
        """Test setting edge type."""
        wrapper = QDMGraphicsEdgeModel(edge_model, mock_graphics_edge)
        wrapper.set_type(EdgeModel.STRAIGHT)
        assert edge_model.edge_type == EdgeModel.STRAIGHT

    def test_is_connected(self, edge_model, mock_graphics_edge, socket_model):
        """Test is_connected check."""
        wrapper = QDMGraphicsEdgeModel(edge_model, mock_graphics_edge)
        
        # Initially not connected
        assert not wrapper.is_connected()
        
        # After connecting
        edge_model.start_socket = socket_model
        edge_model.end_socket = socket_model
        assert wrapper.is_connected()

    def test_type_changed_signal(self, edge_model, mock_graphics_edge):
        """Test edge type changed signal."""
        wrapper = QDMGraphicsEdgeModel(edge_model, mock_graphics_edge)
        signal_received = []
        wrapper.typeChanged.connect(lambda t: signal_received.append(t))

        edge_model.typeChanged.emit(EdgeModel.STRAIGHT)
        assert len(signal_received) > 0


# ======================== QDMGraphicsSocketModel Tests ========================

class TestQDMGraphicsSocketModel:
    """Test suite for QDMGraphicsSocketModel."""

    def test_initialization(self, socket_model, mock_graphics_socket):
        """Test graphics socket model initialization."""
        wrapper = QDMGraphicsSocketModel(socket_model, mock_graphics_socket)
        assert wrapper.model is socket_model
        assert wrapper.graphics_item is mock_graphics_socket

    def test_initialization_with_invalid_model(self, mock_graphics_socket):
        """Test initialization fails with invalid model."""
        invalid_model = object()  # Not a SocketModel
        with pytest.raises((TypeError, AttributeError)):
            QDMGraphicsSocketModel(invalid_model, mock_graphics_socket)  # type: ignore

    def test_socket_id_property(self, socket_model, mock_graphics_socket):
        """Test socket_id property."""
        wrapper = QDMGraphicsSocketModel(socket_model, mock_graphics_socket)
        assert wrapper.socket_id == socket_model.id

    def test_socket_type_property(self, socket_model, mock_graphics_socket):
        """Test socket_type property."""
        wrapper = QDMGraphicsSocketModel(socket_model, mock_graphics_socket)
        assert wrapper.socket_type == SocketModel.INPUT

    def test_is_input_output(self, mock_graphics_socket):
        """Test is_input and is_output properties."""
        input_socket = SocketModel("in", SocketModel.INPUT)
        output_socket = SocketModel("out", SocketModel.OUTPUT)

        input_wrapper = QDMGraphicsSocketModel(input_socket, mock_graphics_socket)
        output_wrapper = QDMGraphicsSocketModel(output_socket, mock_graphics_socket)

        assert input_wrapper.is_input
        assert not input_wrapper.is_output
        assert output_wrapper.is_output
        assert not output_wrapper.is_input

    def test_validation_error_handling(self, socket_model, mock_graphics_socket):
        """Test validation error handling."""
        wrapper = QDMGraphicsSocketModel(socket_model, mock_graphics_socket)
        
        wrapper.set_validation_error("Invalid connection")
        assert not socket_model.is_valid
        assert socket_model.validation_error == "Invalid connection"
        
        wrapper.clear_validation()
        assert socket_model.is_valid


# ======================== QDMGraphicsSceneModel Tests ========================

class TestQDMGraphicsSceneModel:
    """Test suite for QDMGraphicsSceneModel."""

    def test_initialization(self, scene_model, mock_graphics_scene):
        """Test graphics scene model initialization."""
        coordinator = QDMGraphicsSceneModel(scene_model, mock_graphics_scene)
        assert coordinator.scene_model is scene_model
        assert coordinator.graphics_scene is mock_graphics_scene
        assert coordinator.node_count() == 0
        assert coordinator.edge_count() == 0

    def test_initialization_with_invalid_model(self, mock_graphics_scene):
        """Test initialization fails with invalid model."""
        invalid_model = object()  # Not a SceneModel
        with pytest.raises((TypeError, AttributeError)):
            QDMGraphicsSceneModel(invalid_model, mock_graphics_scene)  # type: ignore

    def test_register_node_graphics(self, scene_model, mock_graphics_scene, node_model, mock_graphics_node):
        """Test registering node graphics."""
        coordinator = QDMGraphicsSceneModel(scene_model, mock_graphics_scene)
        
        wrapper = coordinator.register_node_graphics(node_model, mock_graphics_node)
        
        assert wrapper is not None
        assert coordinator.node_count() == 1
        assert coordinator.get_node_wrapper(node_model.id) is wrapper

    def test_register_duplicate_node_graphics(self, scene_model, mock_graphics_scene, node_model, mock_graphics_node):
        """Test registering duplicate node graphics fails."""
        coordinator = QDMGraphicsSceneModel(scene_model, mock_graphics_scene)
        
        coordinator.register_node_graphics(node_model, mock_graphics_node)
        
        with pytest.raises(ValueError):
            coordinator.register_node_graphics(node_model, mock_graphics_node)

    def test_unregister_node_graphics(self, scene_model, mock_graphics_scene, node_model, mock_graphics_node):
        """Test unregistering node graphics."""
        coordinator = QDMGraphicsSceneModel(scene_model, mock_graphics_scene)
        
        coordinator.register_node_graphics(node_model, mock_graphics_node)
        assert coordinator.node_count() == 1
        
        coordinator.unregister_node_graphics(node_model.id)
        assert coordinator.node_count() == 0

    def test_register_edge_graphics(self, scene_model, mock_graphics_scene, edge_model, mock_graphics_edge):
        """Test registering edge graphics."""
        coordinator = QDMGraphicsSceneModel(scene_model, mock_graphics_scene)
        
        wrapper = coordinator.register_edge_graphics(edge_model, mock_graphics_edge)
        
        assert wrapper is not None
        assert coordinator.edge_count() == 1

    def test_register_socket_graphics(self, scene_model, mock_graphics_scene, socket_model, mock_graphics_socket):
        """Test registering socket graphics."""
        coordinator = QDMGraphicsSceneModel(scene_model, mock_graphics_scene)
        
        wrapper = coordinator.register_socket_graphics(socket_model, mock_graphics_socket)
        
        assert wrapper is not None
        assert coordinator.socket_count() == 1

    def test_get_all_wrappers(self, scene_model, mock_graphics_scene, node_model, edge_model, socket_model, mock_graphics_node, mock_graphics_edge, mock_graphics_socket):
        """Test getting all wrappers."""
        coordinator = QDMGraphicsSceneModel(scene_model, mock_graphics_scene)
        
        coordinator.register_node_graphics(node_model, mock_graphics_node)
        coordinator.register_edge_graphics(edge_model, mock_graphics_edge)
        coordinator.register_socket_graphics(socket_model, mock_graphics_socket)
        
        assert len(coordinator.get_all_node_wrappers()) == 1
        assert len(coordinator.get_all_edge_wrappers()) == 1
        assert len(coordinator.get_all_socket_wrappers()) == 1

    def test_scene_cleared(self, scene_model, mock_graphics_scene, node_model, edge_model, socket_model, mock_graphics_node, mock_graphics_edge, mock_graphics_socket):
        """Test scene cleared event."""
        coordinator = QDMGraphicsSceneModel(scene_model, mock_graphics_scene)
        
        coordinator.register_node_graphics(node_model, mock_graphics_node)
        coordinator.register_edge_graphics(edge_model, mock_graphics_edge)
        coordinator.register_socket_graphics(socket_model, mock_graphics_socket)
        
        assert coordinator.node_count() == 1
        
        scene_model.cleared.emit()
        
        assert coordinator.node_count() == 0
        assert coordinator.edge_count() == 0
        assert coordinator.socket_count() == 0
