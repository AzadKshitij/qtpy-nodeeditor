"""
Test suite for MVC backward compatibility and integration.

Tests that refactored classes maintain backward compatibility and integrate properly.
"""

from PyQt6.QtCore import QPointF, QSizeF
import pytest
from nodeeditor.models import (
    NodeModel, EdgeModel, SocketModel, SceneModel,
    GroupNodeModel, EdgeDraggingModel
)
from nodeeditor.controllers import (
    NodeController, EdgeController, SceneController,
    GroupNodeController, scene_controller
)


class TestBackwardCompatibility:
    """Test backward compatibility of refactored classes"""

    def test_node_model_property_access(self):
        """Test that all NodeModel properties are accessible"""
        node = NodeModel("test_type", "Test Node")

        # Properties that should exist
        assert hasattr(node, 'id')
        assert hasattr(node, 'node_type')
        assert hasattr(node, 'title')
        assert hasattr(node, 'position')
        assert hasattr(node, 'x')
        assert hasattr(node, 'y')
        assert hasattr(node, 'selected')
        assert hasattr(node, 'visible')

    def test_socket_model_property_access(self):
        """Test that all SocketModel properties are accessible"""
        socket = SocketModel("test", SocketModel.INPUT)

        # Properties that should exist
        assert hasattr(socket, 'id')
        assert hasattr(socket, 'name')
        assert hasattr(socket, 'is_input')
        assert hasattr(socket, 'is_output')
        assert hasattr(socket, 'socket_type')
        assert hasattr(socket, 'is_connected')

    def test_edge_model_property_access(self):
        """Test that all EdgeModel properties are accessible"""
        socket1 = SocketModel("out", SocketModel.OUTPUT)
        socket2 = SocketModel("in", SocketModel.INPUT)
        edge = EdgeModel(socket1, socket2)

        # Properties that should exist
        assert hasattr(edge, 'id')
        assert hasattr(edge, 'start_socket')
        assert hasattr(edge, 'end_socket')
        assert hasattr(edge, 'is_connected')

    def test_node_model_method_compatibility(self):
        """Test that NodeModel methods work as expected"""
        node = NodeModel("test", "Node")

        # Methods that should exist
        assert callable(getattr(node, 'serialize', None))
        assert callable(getattr(node, 'deserialize', None))
        assert callable(getattr(node, 'set_property', None))
        assert callable(getattr(node, 'get_property', None))

    def test_edge_model_method_compatibility(self):
        """Test that EdgeModel methods work as expected"""
        socket1 = SocketModel("out", SocketModel.OUTPUT)
        socket2 = SocketModel("in", SocketModel.INPUT)
        edge = EdgeModel(socket1, socket2)

        # Methods that should exist
        assert callable(getattr(edge, 'serialize', None))
        assert callable(getattr(edge, 'deserialize', None))

    def test_socket_model_edge_management(self):
        """Test that socket can manage edges (backward compatibility)"""
        socket = SocketModel("test", SocketModel.INPUT)
        edge1 = EdgeModel()
        edge2 = EdgeModel()

        assert callable(getattr(socket, 'add_edge', None))
        assert callable(getattr(socket, 'remove_edge', None))
        assert callable(getattr(socket, 'get_edges', None))

        socket.add_edge(edge1)
        socket.add_edge(edge2)
        edges = socket.get_edges()
        assert edge1 in edges
        assert edge2 in edges

    def test_controller_delegation_to_model(self):
        """Test that controllers properly delegate to models"""
        node_model = NodeModel("test", "Node")
        scene_model = SceneModel()
        controller = NodeController(scene_model)

        # Controller methods should update model
        controller.set_node_title(node_model, "New Title")
        assert node_model.title == "New Title"

        controller.set_node_position(node_model, (100.0, 200.0))
        assert node_model.position == (100.0, 200.0)

    def test_group_node_model_backward_compat(self):
        """Test GroupNodeModel backward compatibility"""
        group = GroupNodeModel(1, "Test Group")

        # Properties
        assert hasattr(group, 'title')
        assert hasattr(group, 'is_collapsed')
        assert hasattr(group, 'child_node_ids')
        assert hasattr(group, 'position')
        assert hasattr(group, 'size')

        # Methods
        assert callable(getattr(group, 'add_child_node', None))
        assert callable(getattr(group, 'remove_child_node', None))
        assert callable(getattr(group, 'serialize', None))


class TestIntegrationWithLegacyCode:
    """Test integration of MVC with existing code patterns"""

    def test_node_serialization_deserialization_roundtrip(self):
        """Test that serialization roundtrip preserves state"""
        node1 = NodeModel("custom_type", "Test Node")
        node1.position = (123.45, 567.89)
        node1.selected = True
        node1.set_property("custom_prop", "custom_value")
        
        # Serialize
        data = node1.serialize()
        
        # Deserialize
        node2 = NodeModel.deserialize(data)
        
        # Verify all properties preserved
        assert node2.node_type == "custom_type"
        assert node2.title == "Test Node"
        assert node2.position == (123.45, 567.89)
        assert node2.selected is True
        assert node2.get_property("custom_prop") == "custom_value"

    def test_edge_with_mixed_socket_types(self):
        """Test edge handling with different socket implementations"""
        # Create sockets using SocketModel directly
        out_socket = SocketModel("output", SocketModel.OUTPUT)
        in_socket = SocketModel("input", SocketModel.INPUT)
        
        # Create edge connecting them
        edge = EdgeModel(out_socket, in_socket)
        
        # Edge should properly reference both sockets
        assert edge.start_socket == out_socket
        assert edge.end_socket == in_socket
        assert edge.is_connected

    def test_scene_with_nodes_and_edges(self):
        """Test creating and managing a simple scene"""
        scene = SceneModel()
        
        # Create nodes
        node1_model = NodeModel("type1", "Node1")
        node2_model = NodeModel("type2", "Node2")
        
        # Create sockets
        out_socket = SocketModel("out", SocketModel.OUTPUT)
        in_socket = SocketModel("in", SocketModel.INPUT)
        
        # Create edge
        edge = EdgeModel(out_socket, in_socket)
        
        # Edge should be properly configured
        assert edge.start_socket == out_socket
        assert edge.end_socket == in_socket

    def test_group_with_node_references(self):
        """Test group managing references to nodes"""
        group = GroupNodeModel("Container")
        controller = GroupNodeController(group)
        
        # Add node IDs to group
        node_ids = [NodeModel("node_1"), NodeModel("node_2"), NodeModel("node_3")]
        for node_id in node_ids:
            controller.add_node(node_id)
        
        # Verify all nodes are tracked
        assert len(group.child_node_ids) == len(node_ids)
        for node in node_ids:
            assert node.id in group.child_node_ids


class TestDataConsistency:
    """Test data consistency across MVC operations"""

    def test_model_state_consistency_after_updates(self):
        """Test that model state remains consistent after multiple updates"""
        node = NodeModel("test", "Initial")

        updates = [
            ("title", "Node1"),
            ("title", "Node2"),
            ("position", (100.0, 100.0)),
            ("title", "Node3"),
            ("position", (200.0, 200.0)),
        ]

        for prop, value in updates:
            if prop == "title":
                node.title = value
            elif prop == "position":
                node.position = value

        # Final state should reflect last update
        assert node.title == "Node3"
        assert node.position == (200.0, 200.0)

    def test_socket_edge_list_consistency(self):
        """Test that socket edge list remains consistent"""
        socket = SocketModel("test", SocketModel.INPUT)
        edges = []

        # Add edges
        for i in range(5):
            edge = EdgeModel()
            socket.add_edge(edge)
            edges.append(edge)

        # Verify all present
        socket_edges = socket.get_edges()
        assert len(socket_edges) == 5
        for edge in edges:
            assert edge in socket_edges

        # Remove one
        socket.remove_edge(edges[2])
        socket_edges = socket.get_edges()
        assert len(socket_edges) == 4
        assert edges[2] not in socket_edges

    def test_group_child_node_list_consistency(self):
        """Test that group child node list remains consistent"""
        group = GroupNodeModel("Group")

        node_ids = [NodeModel("node_1"), NodeModel("node_2"), NodeModel("node_3"), NodeModel("node_4"), NodeModel("node_5")]

        # Add all nodes
        for node_id in node_ids:
            group.add_child_node(int(node_id.id))

        # Verify all present
        assert len(group.child_node_ids) == 5

        # Remove some
        group.remove_child_node(int(node_ids[1].id))
        group.remove_child_node(int(node_ids[3].id))

        # Verify remaining
        assert len(group.child_node_ids) == 3
        assert node_ids[1].id not in group.child_node_ids
        assert node_ids[3].id not in group.child_node_ids
        assert int(node_ids[0].id) in group.child_node_ids

    def test_controller_model_sync(self):
        """Test that controller changes are reflected in model"""
        model = NodeModel("test", "Node")
        controller = NodeController(model)

        # Make changes through controller
        controller.set_title("Controller Title")
        controller.set_position(111.11, 222.22)
        controller.set_selected(True)
        controller.set_visible(False)

        # Verify model reflects changes
        assert model.title == "Controller Title"
        assert model.position == (111.11, 222.22)
        assert model.selected is True
        assert model.visible is False

    def test_group_controller_model_sync(self):
        """Test that group controller changes sync with model"""
        model = GroupNodeModel("Group")
        controller = GroupNodeController(model)

        # Make changes through controller
        controller.set_title("New Title")
        controller.set_position(50.0, 75.0)
        controller.set_size(300.0, 250.0)
        controller.add_node_by_id(1)
        controller.add_node_by_id(2)
        controller.collapse()

        # Verify model reflects all changes
        assert model.title == "New Title"
        assert model.position == QPointF(50.0, 75.0)
        assert model.size == QSizeF(300.0, 250.0)
        assert len(model.child_node_ids) == 2
        assert model.is_collapsed is True


class TestEdgeCases:
    """Test edge cases and corner scenarios"""

    def test_empty_node_title(self):
        """Test node with empty title"""
        node = NodeModel("test", "")
        assert node.title == ""
        
        node.title = "NoLongerEmpty"
        assert node.title == "NoLongerEmpty"

    def test_node_negative_position(self):
        """Test node with negative position"""
        node = NodeModel("test", "Node")
        node.position = (-100.0, -200.0)
        assert node.position == (-100.0, -200.0)
        assert node.x == -100.0
        assert node.y == -200.0

    def test_zero_size_group(self):
        """Test group with zero size"""
        group = GroupNodeModel("Group")
        group.size = QSizeF(0.0, 0.0)
        assert group.size == QSizeF(0.0, 0.0)

    def test_group_with_no_children(self):
        """Test empty group operations"""
        group = GroupNodeModel("Empty")
        assert len(group.child_node_ids) == 0
        
        # Remove from empty should not crash
        group.remove_child_node("nonexistent")
        assert len(group.child_node_ids) == 0

    def test_socket_with_special_characters_in_name(self):
        """Test socket with special characters in name"""
        special_names = [
            "socket-with-dash",
            "socket.with.dot",
            "socket_with_underscore",
            "socket(with)parens",
            "socket[with]brackets",
        ]
        
        for name in special_names:
            socket = SocketModel(name, SocketModel.INPUT)
            assert socket.name == name

    def test_node_property_with_complex_values(self):
        """Test node properties with complex values"""
        node = NodeModel("test", "Node")
        
        # Store complex types
        node.set_property("list", [1, 2, 3])
        node.set_property("dict", {"key": "value"})
        node.set_property("tuple", (1, 2))
        node.set_property("nested", {"list": [1, 2, {"deep": "value"}]})
        
        assert node.get_property("list") == [1, 2, 3]
        assert node.get_property("dict") == {"key": "value"}
        assert node.get_property("tuple") == (1, 2)
        assert node.get_property("nested") == {"list": [1, 2, {"deep": "value"}]}

    def test_rapid_state_changes(self):
        """Test rapid consecutive state changes"""
        node = NodeModel("test", "Node")
        titles = []
        node.titleChanged.connect(lambda t: titles.append(t))
        
        # Rapid changes
        for i in range(100):
            node.title = f"Title_{i}"
        
        assert len(titles) == 100
        assert node.title == "Title_99"
