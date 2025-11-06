"""
Test suite for GroupNode MVC integration.

Tests GroupNodeModel, GroupNodeController, and GroupNode wrapper class.
"""

from qtpy.QtCore import QSizeF
import pytest
from qtpy.QtCore import Qt, QRectF, QPointF
from nodeeditor.models import GroupNodeModel
from nodeeditor.models.node_model import NodeModel
from nodeeditor.controllers import GroupNodeController


class TestGroupNodeModel:
    """Test cases for GroupNodeModel"""

    def test_create_group_node_model(self):
        """Test creating a GroupNodeModel"""
        model = GroupNodeModel(1, "test_group")

        assert model.title == "test_group"
        assert not model.is_collapsed
        assert model.child_node_ids == []
        assert (model.position.x(), model.position.y()) == (0.0, 0.0)
        assert (model.size.width(), model.size.height()) == (200.0, 150.0)

    def test_group_node_title(self):
        """Test setting group node title"""
        model = GroupNodeModel(2, "Original")
        signals_received = []

        model.titleChanged.connect(lambda title: signals_received.append(title))
        model.title = "Updated"

        assert model.title == "Updated"
        assert len(signals_received) == 1
        assert signals_received[0] == "Updated"

    def test_group_node_collapsed(self):
        """Test collapsing and expanding group"""
        model = GroupNodeModel(3, "Group")
        signals_received = []

        model.collapsedChanged.connect(lambda is_collapsed: signals_received.append(is_collapsed))

        model.is_collapsed = True
        assert model.is_collapsed
        assert len(signals_received) == 1
        assert signals_received[0] is True

        model.is_collapsed = False
        assert not model.is_collapsed
        assert len(signals_received) == 2
        assert signals_received[1] is False

    def test_group_node_position(self):
        """Test setting group position"""
        model = GroupNodeModel(4, "Group")
        signals_received = []

        model.positionChanged.connect(lambda pos: signals_received.append(pos))
        model.position = QPointF(100.0, 200.0)

        assert (model.position.x(), model.position.y()) == (100.0, 200.0)
        assert len(signals_received) == 1

    def test_group_node_size(self):
        """Test setting group size"""
        model = GroupNodeModel(5, "Group")
        signals_received = []

        model.sizeChanged.connect(lambda size: signals_received.append(size))
        model.size = QSizeF(300.0, 250.0)

        assert (model.size.width(), model.size.height()) == (300.0, 250.0)
        assert len(signals_received) == 1

    def test_add_child_node(self):
        """Test adding child nodes"""
        model = GroupNodeModel(6, "Group")
        signals_received = []
        model.childNodesChanged.connect(lambda: signals_received.append("changed"))
        model.add_child_node(1)
        assert 1 in model.child_node_ids
        assert len(signals_received) == 1
        model.add_child_node(2)
        assert 2 in model.child_node_ids
        assert len(signals_received) == 2

    def test_remove_child_node(self):
        """Test removing child nodes"""
        model = GroupNodeModel(7, "Group")
        signals_received = []
        model.childNodesChanged.connect(lambda: signals_received.append("changed"))
        model.add_child_node(1)
        model.add_child_node(2)
        signals_received.clear()
        model.remove_child_node(1)
        assert 1 not in model.child_node_ids
        assert 2 in model.child_node_ids
        assert len(signals_received) == 1

    def test_clear_child_nodes(self):
        """Test clearing all child nodes"""
        model = GroupNodeModel(8, "Group")
        model.add_child_node(1)
        model.add_child_node(2)
        assert len(model.child_node_ids) == 2
        model._child_node_ids.clear()  # Directly clear for test
        assert len(model.child_node_ids) == 0

    def test_group_boundaries(self):
        """Test setting group boundaries"""
        model = GroupNodeModel(9, "Group")
        signals_received = []

        model.boundariesChanged.connect(lambda rect: signals_received.append(rect))

        model.set_boundaries(10, 20, 300, 250)

        assert len(signals_received) == 1
        emitted_rect = signals_received[0]
        assert isinstance(emitted_rect, QRectF)
        assert emitted_rect == model.rect

    def test_group_model_serialization(self):
        """Test serializing and deserializing GroupNodeModel"""
        model1 = GroupNodeModel(10, "Test Group")
        model1.position = QPointF(50.0, 75.0)
        model1.size = QSizeF(250.0, 200.0)
        model1.add_child_node(1)
        model1.add_child_node(2)
        model1.is_collapsed = True

        # Serialize
        data = model1.serialize()

        # Deserialize
        model2 = GroupNodeModel(11, "Temp")
        assert model2.deserialize(data)
        assert model2.title == "Test Group"
        assert (model2.position.x(), model2.position.y()) == (50.0, 75.0)
        assert (model2.size.width(), model2.size.height()) == (250.0, 200.0)
        assert len(model2.child_node_ids) == 2
        assert model2.is_collapsed

    def test_color_properties(self):
        """Test color properties"""
        # def test_group_boundaries(self):
        #     """Test setting group boundaries"""
        #     model = GroupNodeModel(9, "Group")
        #     signals_received = []
        #     model.boundariesChanged.connect(lambda rect: signals_received.append(rect))
        #     rect = QRectF(10, 20, 300, 250)
        #     model.boundaries = rect
        #     assert model.boundaries == rect
        #     assert len(signals_received) == 1
        model = GroupNodeModel(11, "Group")

        # Test getting default colors (should not raise)
        color = model.color
        assert color is not None

        title_color = model.title_color
        assert title_color is not None

        border_color = model.border_color
        assert border_color is not None

    def test_multiple_state_changes(self):
        """Test multiple state changes trigger appropriate signals"""
        model = GroupNodeModel(12, "Group")

        title_changes = []
        collapse_changes = []
        position_changes = []

        model.titleChanged.connect(lambda t: title_changes.append(t))
        model.collapsedChanged.connect(lambda c: collapse_changes.append(c))
        model.positionChanged.connect(lambda p: position_changes.append(p))

        model.title = "Updated"
        model.is_collapsed = True
        model.position = QPointF(100.0, 200.0)
        model.is_collapsed = False
        model.title = "Final"

        assert len(title_changes) == 2
        assert len(collapse_changes) == 2
        assert len(position_changes) == 1


class TestGroupNodeController:
    """Test cases for GroupNodeController"""

    def test_create_group_node_controller(self):
        model = GroupNodeModel(13, "Group")
        controller = GroupNodeController(model)

        assert controller.model is model

    def test_add_node_to_group(self):
        model = GroupNodeModel(14, "Group")
        controller = GroupNodeController(model)
        node1 = NodeModel("typeA", "Node 1")
        node2 = NodeModel("typeA", "Node 2")

        controller.add_node(node1)
        controller.add_node(node2)

        child_ids = model.child_node_ids
        assert node1.id in child_ids
        assert node2.id in child_ids

    def test_remove_node_from_group(self):
        model = GroupNodeModel(15, "Group")
        controller = GroupNodeController(model)
        node1 = NodeModel("typeA", "Node 1")
        node2 = NodeModel("typeA", "Node 2")

        controller.add_node(node1)
        controller.add_node(node2)
        controller.remove_node(node1)

        child_ids = model.child_node_ids
        assert node1.id not in child_ids
        assert node2.id in child_ids

    def test_set_title(self):
        model = GroupNodeModel(16, "Original")
        controller = GroupNodeController(model)

        controller.set_title("Updated")

        assert model.title == "Updated"

    def test_set_position(self):
        model = GroupNodeModel(17, "Group")
        controller = GroupNodeController(model)

        controller.set_position(100.0, 200.0)

        assert (model.position.x(), model.position.y()) == (100.0, 200.0)

    def test_set_size(self):
        model = GroupNodeModel(18, "Group")
        controller = GroupNodeController(model)

        controller.set_size(300.0, 250.0)

        assert (model.size.width(), model.size.height()) == (300.0, 250.0)

    def test_collapse_group(self):
        model = GroupNodeModel(19, "Group")
        controller = GroupNodeController(model)

        controller.collapse()

        assert model.is_collapsed

    def test_expand_group(self):
        model = GroupNodeModel(20, "Group")
        controller = GroupNodeController(model)
        model.is_collapsed = True

        controller.expand()

        assert not model.is_collapsed

    def test_toggle_collapse(self):
        model = GroupNodeModel(21, "Group")
        controller = GroupNodeController(model)

        controller.toggle_collapse()
        assert model.is_collapsed

        controller.toggle_collapse()
        assert not model.is_collapsed

    def test_set_boundaries(self):
        model = GroupNodeModel(22, "Group")
        controller = GroupNodeController(model)

        controller.set_boundaries(10, 20, 300, 250)

        rect = model.rect
        assert (rect.x(), rect.y(), rect.width(), rect.height()) == (10.0, 20.0, 300.0, 250.0)

    def test_set_color(self):
        model = GroupNodeModel(23, "Group")
        controller = GroupNodeController(model)

        controller.set_color(255, 0, 0, 180)

        assert model.color.red() == 255
        assert model.color.green() == 0
        assert model.color.blue() == 0
        assert model.color.alpha() == 180

    def test_serialize_group(self):
        model = GroupNodeModel(24, "Group")
        controller = GroupNodeController(model)
        controller.set_position(50.0, 75.0)
        controller.set_size(250.0, 200.0)
        node = NodeModel("typeA", "Node 1")
        controller.add_node(node)

        data = controller.serialize()

        assert isinstance(data, dict)
        assert data["title"] == "Group"
        assert data["x"] == 50.0
        assert data["y"] == 75.0
        assert data["width"] == 250.0
        assert data["height"] == 200.0
        assert node.id in data["child_node_ids"]

    def test_deserialize_group(self):
        model1 = GroupNodeModel(25, "Test Group")
        controller1 = GroupNodeController(model1)
        controller1.set_position(50.0, 75.0)
        controller1.set_size(250.0, 200.0)
        node = NodeModel("typeA", "Node 1")
        controller1.add_node(node)

        data = controller1.serialize()

        model2 = GroupNodeModel(26, "Placeholder")
        controller2 = GroupNodeController(model2)

        assert controller2.deserialize(data)
        assert model2.title == "Test Group"
        assert (model2.position.x(), model2.position.y()) == (50.0, 75.0)
        assert (model2.size.width(), model2.size.height()) == (250.0, 200.0)
        assert node.id in model2.child_node_ids


class TestGroupNodeIntegration:
    """Integration tests for GroupNode operations"""

    def test_group_with_multiple_children(self):
        model = GroupNodeModel(26, "Container")
        controller = GroupNodeController(model)

        nodes = [NodeModel("typeA", f"Node {i}") for i in range(1, 6)]
        for node in nodes:
            controller.add_node(node)

        assert len(model.child_node_ids) == 5
        assert {node.id for node in nodes} == set(model.child_node_ids)

    def test_group_lifecycle(self):
        model = GroupNodeModel(27, "Group")
        controller = GroupNodeController(model)

        controller.set_position(100.0, 100.0)
        controller.set_size(200.0, 200.0)
        controller.set_title("Test Group")

        node1 = NodeModel("typeA", "Node 1")
        node2 = NodeModel("typeA", "Node 2")
        controller.add_node(node1)
        controller.add_node(node2)

        assert {node1.id, node2.id} == set(model.child_node_ids)
        assert model.title == "Test Group"

        controller.collapse()
        assert model.is_collapsed

        controller.expand()
        assert not model.is_collapsed

        controller.remove_node(node1)
        assert set(model.child_node_ids) == {node2.id}

    def test_group_model_consistency(self):
        model = GroupNodeModel(28, "Group")
        controller = GroupNodeController(model)

        initial_title = model.title
        initial_pos = (model.position.x(), model.position.y())
        initial_size = (model.size.width(), model.size.height())

        controller.set_title("New Title")
        controller.set_position(50.0, 75.0)
        controller.set_size(250.0, 200.0)
        node1 = NodeModel("typeA", "Node 1")
        node2 = NodeModel("typeA", "Node 2")
        controller.add_node(node1)
        controller.add_node(node2)

        assert model.title == "New Title"
        assert model.title != initial_title
        assert (model.position.x(), model.position.y()) == (50.0, 75.0)
        assert (model.position.x(), model.position.y()) != initial_pos
        assert (model.size.width(), model.size.height()) == (250.0, 200.0)
        assert (model.size.width(), model.size.height()) != initial_size
        assert {node1.id, node2.id} == set(model.child_node_ids)

    def test_group_node_ids_persistence(self):
        model = GroupNodeModel(29, "Group")
        controller = GroupNodeController(model)

        nodes = [NodeModel("typeA", f"Node {label}") for label in ["A", "B", "C"]]
        for node in nodes:
            controller.add_node(node)

        assert {node.id for node in nodes} == set(model.child_node_ids)
        assert len(model.child_node_ids) == len(nodes)

    def test_signal_flow_on_group_operations(self):
        model = GroupNodeModel(30, "Group")

        title_signals: list[str] = []
        position_signals: list[QPointF] = []
        size_signals: list[QSizeF] = []
        child_signals: list[list[int]] = []

        model.titleChanged.connect(lambda t: title_signals.append(t))
        model.positionChanged.connect(lambda p: position_signals.append(p))
        model.sizeChanged.connect(lambda s: size_signals.append(s))
        model.childNodesChanged.connect(lambda ids: child_signals.append(ids))

        controller = GroupNodeController(model)

        controller.set_title("New Title")
        controller.set_position(100.0, 200.0)
        controller.set_size(250.0, 200.0)
        node = NodeModel("typeA", "Node 1")
        controller.add_node(node)

        assert len(title_signals) == 1 and title_signals[0] == "New Title"
        assert len(position_signals) == 1 and (position_signals[0].x(), position_signals[0].y()) == (100.0, 200.0)
        assert len(size_signals) == 1 and (size_signals[0].width(), size_signals[0].height()) == (250.0, 200.0)
        assert len(child_signals) == 1 and node.id in child_signals[0]
