"""
Test suite for MVC Model layer.

Tests NodeModel, EdgeModel, SocketModel, and SceneModel classes.
"""

import pytest
from nodeeditor.models import NodeModel, EdgeModel, SocketModel, SceneModel


class TestNodeModel:
    """Test cases for NodeModel"""

    def test_create_node(self):
        """Test creating a basic node"""
        node = NodeModel("test_type", "Test Node")
        assert node.node_type == "test_type"
        assert node.title == "Test Node"
        assert node.position == (0.0, 0.0)
        assert not node.selected
        assert node.visible

    def test_node_position(self):
        """Test setting node position"""
        node = NodeModel("test", "Node")
        node.position = (100.0, 200.0)
        assert node.position == (100.0, 200.0)
        assert node.x == 100.0
        assert node.y == 200.0

    def test_node_title_signal(self):
        """Test title change signal"""
        node = NodeModel("test", "Original")
        signals_received = []
        
        node.titleChanged.connect(lambda title: signals_received.append(title))
        node.title = "Updated"
        
        assert len(signals_received) == 1
        assert signals_received[0] == "Updated"
        assert node.title == "Updated"

    def test_node_properties(self):
        """Test custom properties"""
        node = NodeModel("test", "Node")
        
        node.set_property("color", "red")
        assert node.get_property("color") == "red"
        assert node.has_property("color")
        
        node.set_property("value", 42)
        assert node.get_property("value") == 42
        
        all_props = node.get_all_properties()
        assert all_props == {"color": "red", "value": 42}

    def test_node_serialization(self):
        """Test serializing and deserializing a node"""
        node1 = NodeModel("test_type", "Test Node")
        node1.position = (50.0, 75.0)
        node1.set_property("custom", "data")
        node1.selected = True
        
        # Serialize
        data = node1.serialize()
        
        # Deserialize
        node2 = NodeModel.deserialize(data)
        assert node2.node_type == "test_type"
        assert node2.title == "Test Node"
        assert node2.position == (50.0, 75.0)
        assert node2.get_property("custom") == "data"
        assert node2.selected

    def test_node_equality(self):
        """Test node equality based on ID"""
        node1 = NodeModel("test", "Node1")
        node2 = NodeModel("test", "Node2")
        
        assert node1 != node2
        assert node1 == node1


class TestSocketModel:
    """Test cases for SocketModel"""

    def test_create_socket(self):
        """Test creating a socket"""
        socket = SocketModel("input", SocketModel.INPUT)
        assert socket.name == "input"
        assert socket.is_input
        assert not socket.is_output
        assert not socket.is_connected

    def test_socket_edges(self):
        """Test adding/removing edges"""
        socket = SocketModel("test", SocketModel.INPUT)
        edge = EdgeModel()
        
        assert socket.add_edge(edge)
        assert socket.is_connected
        assert socket.edge_count == 1
        assert edge in socket.edges
        
        assert socket.remove_edge(edge)
        assert not socket.is_connected

    def test_socket_validation(self):
        """Test socket validation state"""
        socket = SocketModel("test", SocketModel.INPUT)
        signals_received = []
        
        socket.validationChanged.connect(
            lambda valid, msg: signals_received.append((valid, msg))
        )
        
        socket.set_valid(False, "Error message")
        assert not socket.is_valid
        assert socket.validation_error == "Error message"
        assert len(signals_received) == 1

    def test_socket_parent_node(self):
        """Test socket parent node reference"""
        node = NodeModel("test", "Node")
        socket = SocketModel("input", SocketModel.INPUT, parent_node=node)
        
        assert socket.parent_node == node
        assert socket.parent_node.id == node.id


class TestEdgeModel:
    """Test cases for EdgeModel"""

    def test_create_edge(self):
        """Test creating an edge"""
        edge = EdgeModel()
        assert edge.edge_type == EdgeModel.BEZIER
        assert not edge.is_connected

    def test_edge_connection(self):
        """Test connecting sockets"""
        socket1 = SocketModel("out", SocketModel.OUTPUT)
        socket2 = SocketModel("in", SocketModel.INPUT)
        edge = EdgeModel()
        
        edge.start_socket = socket1
        edge.end_socket = socket2
        
        assert edge.is_connected
        assert edge.start_socket == socket1
        assert edge.end_socket == socket2

    def test_edge_type(self):
        """Test changing edge type"""
        edge = EdgeModel()
        signals_received = []
        
        edge.typeChanged.connect(lambda t: signals_received.append(t))
        edge.edge_type = EdgeModel.STRAIGHT
        
        assert edge.edge_type == EdgeModel.STRAIGHT
        assert edge.get_edge_type_name() == "STRAIGHT"
        assert len(signals_received) == 1

    def test_edge_validation(self):
        """Test edge connection validation"""
        socket1 = SocketModel("out", SocketModel.OUTPUT)
        socket2 = SocketModel("in", SocketModel.INPUT)
        edge = EdgeModel()
        
        # Invalid: not connected
        valid, msg = edge.validate_connection()
        assert not valid
        
        # Valid connection
        edge.start_socket = socket1
        edge.end_socket = socket2
        valid, msg = edge.validate_connection()
        assert valid

    def test_edge_data(self):
        """Test custom edge data"""
        edge = EdgeModel()
        edge.set_data("thickness", 2)
        assert edge.get_data("thickness") == 2


class TestSceneModel:
    """Test cases for SceneModel"""

    def test_create_scene(self):
        """Test creating a scene"""
        scene = SceneModel()
        assert scene.node_count == 0
        assert scene.edge_count == 0
        assert not scene.modified

    def test_add_remove_nodes(self):
        """Test adding and removing nodes"""
        scene = SceneModel()
        node = NodeModel("test", "Node")
        signals_received = []
        
        scene.nodeAdded.connect(lambda n: signals_received.append(n))
        
        assert scene.add_node(node)
        assert scene.node_count == 1
        assert scene.modified
        assert len(signals_received) == 1
        
        assert scene.remove_node(node.id)
        assert scene.node_count == 0

    def test_get_node(self):
        """Test retrieving nodes"""
        scene = SceneModel()
        node = NodeModel("test", "Node")
        scene.add_node(node)
        
        retrieved = scene.get_node(node.id)
        assert retrieved == node

    def test_add_remove_edges(self):
        """Test adding and removing edges"""
        scene = SceneModel()
        
        # Create nodes and sockets
        node1 = NodeModel("test", "Node1")
        node2 = NodeModel("test", "Node2")
        scene.add_node(node1)
        scene.add_node(node2)
        
        socket1 = SocketModel("out", SocketModel.OUTPUT, parent_node=node1)
        socket2 = SocketModel("in", SocketModel.INPUT, parent_node=node2)
        
        # Create and add edge
        edge = EdgeModel()
        edge.start_socket = socket1
        edge.end_socket = socket2
        
        assert scene.add_edge(edge)
        assert scene.edge_count == 1
        
        assert scene.remove_edge(edge.id)
        assert scene.edge_count == 0

    def test_scene_selection(self):
        """Test node selection in scene"""
        scene = SceneModel()
        
        nodes = [
            NodeModel("test", f"Node{i}") for i in range(3)
        ]
        for node in nodes:
            scene.add_node(node)
        
        nodes[0].selected = True
        nodes[1].selected = True
        
        selected = scene.get_selected_nodes()
        assert len(selected) == 2
        
        assert scene.deselect_all_nodes() == 2
        assert len(scene.get_selected_nodes()) == 0

    def test_scene_serialization(self):
        """Test serializing and deserializing a scene"""
        # Create scene with nodes
        scene1 = SceneModel()
        node = NodeModel("test", "TestNode")
        node.position = (100.0, 200.0)
        scene1.add_node(node)
        
        # Serialize
        data = scene1.serialize()
        
        # Deserialize
        scene2 = SceneModel.deserialize(data)
        assert scene2.node_count == 1
        
        recovered_node = scene2.nodes[0]
        assert recovered_node.node_type == "test"
        assert recovered_node.title == "TestNode"

    def test_scene_clear(self):
        """Test clearing the scene"""
        scene = SceneModel()
        
        for i in range(3):
            node = NodeModel("test", f"Node{i}")
            scene.add_node(node)
        
        assert scene.node_count == 3
        scene.clear()
        assert scene.node_count == 0


class TestModelIntegration:
    """Integration tests for all models working together"""

    def test_complete_graph(self):
        """Test building a complete graph"""
        # Create scene
        scene = SceneModel()
        
        # Create nodes
        add_node = NodeModel("add_op", "Add")
        mul_node = NodeModel("mul_op", "Multiply")
        
        scene.add_node(add_node)
        scene.add_node(mul_node)
        
        # Create sockets
        add_out = SocketModel("result", SocketModel.OUTPUT, parent_node=add_node)
        mul_in = SocketModel("factor", SocketModel.INPUT, parent_node=mul_node)
        
        # Create edge
        edge = EdgeModel()
        edge.start_socket = add_out
        edge.end_socket = mul_in
        
        # Register edge with sockets
        add_out.add_edge(edge)
        mul_in.add_edge(edge)
        
        scene.add_edge(edge)
        
        # Verify structure
        assert scene.node_count == 2
        assert scene.edge_count == 1
        assert add_out.is_connected
        assert mul_in.is_connected

    def test_signal_propagation(self):
        """Test signals propagate through the hierarchy"""
        scene = SceneModel()
        scene.modifiedChanged.connect(lambda m: print(f"Scene modified: {m}"))
        
        node = NodeModel("test", "Node")
        node.titleChanged.connect(lambda t: print(f"Title: {t}"))
        
        scene.add_node(node)
        node.title = "Updated"
        
        assert scene.modified
        assert node.title == "Updated"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
