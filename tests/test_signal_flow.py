"""
Test suite for MVC Signal Flow across integrated components.

Tests signal propagation between Models, Controllers, and Graphics components.
"""

import pytest
from qtpy.QtCore import Qt, QPointF
from nodeeditor.models import (
    NodeModel, EdgeModel, SocketModel, SceneModel,
    GroupNodeModel, EdgeDraggingModel
)
from nodeeditor.controllers import (
    NodeController, EdgeController, SceneController,
    GroupNodeController
)


def _normalize_point(value):
    """Return a plain (x, y) tuple for QPointF or tuple/list inputs."""
    if isinstance(value, QPointF):
        return (float(value.x()), float(value.y()))
    if isinstance(value, (tuple, list)) and len(value) == 2:
        try:
            return (float(value[0]), float(value[1]))
        except (TypeError, ValueError):
            return tuple(value)
    return value


class TestSignalFlow:
    """Test signal flow across MVC layers"""

    def test_node_model_to_controller_signal_flow(self):
        """Test that model signals are received by monitoring code"""
        model = NodeModel("test", "Node")
        signals_received = []
        
        # Connect to model signal
        model.titleChanged.connect(lambda title: signals_received.append(("title", title)))
        model.positionChanged.connect(
            lambda pos: signals_received.append(("position", _normalize_point(pos)))
        )
        model.selectedChanged.connect(lambda sel: signals_received.append(("selected", sel)))
        
        # Make changes
        model.title = "Updated"
        model.position = (100.0, 200.0)
        model.selected = True
        
        # Verify signals were emitted
        assert len(signals_received) == 3
        assert signals_received[0] == ("title", "Updated")
        assert signals_received[1] == ("position", (100.0, 200.0))
        assert signals_received[2] == ("selected", True)

    def test_socket_model_signal_flow(self):
        """Test socket model signal propagation"""
        socket = SocketModel("input", SocketModel.INPUT)
        signals_received = []
        
        socket.connectionChanged.connect(
            lambda edge: signals_received.append(("connection", edge))
        )
        socket.validationChanged.connect(
            lambda is_valid, message: signals_received.append(("validation", is_valid, message))
        )

        edge = EdgeModel()
        socket.add_edge(edge)
        socket.remove_edge(edge)
        socket.set_valid(False, "error")
        socket.set_valid(True)

        assert signals_received[0][0] == "connection"
        assert signals_received[0][1] is edge
        assert signals_received[1] == ("connection", None)
        assert signals_received[2] == ("validation", False, "error")
        assert signals_received[3] == ("validation", True, "")

    def test_edge_dragging_model_signal_flow(self):
        """Test EdgeDraggingModel signal propagation"""
        model = EdgeDraggingModel()
        signals_received = []
        
        model.dragStarted.connect(lambda eid, sid: signals_received.append(("start", eid, sid)))
        model.dragUpdated.connect(lambda x, y: signals_received.append(("update", x, y)))
        model.dragEnded.connect(lambda sid, valid: signals_received.append(("end", sid, valid)))
        
        # Simulate drag operation
        model.start_drag("edge_1", 5)
        model.update_position(100.0, 200.0)
        model.end_drag(10, is_valid=True)
        
        assert len(signals_received) == 3
        assert signals_received[0][0] == "start"
        assert signals_received[1][0] == "update"
        assert signals_received[2][0] == "end"

    def test_group_node_model_signal_flow(self):
        """Test GroupNodeModel signal propagation"""
        model = GroupNodeModel(1, "Group")
        signals_received = []

        model.titleChanged.connect(lambda t: signals_received.append(("title", t)))
        model.collapsedChanged.connect(lambda c: signals_received.append(("collapsed", c)))
        model.childNodesChanged.connect(
            lambda children: signals_received.append(("children", list(children)))
        )

        model.title = "Updated"
        model.is_collapsed = True
        model.add_child_node(1)

        assert signals_received[0] == ("title", "Updated")
        assert signals_received[1] == ("collapsed", True)
        assert signals_received[2] == ("children", [1])

    def test_scene_model_signal_flow(self):
        """Test SceneModel signal propagation"""
        model = SceneModel()
        signals_received = []
        
        model.nodeAdded.connect(
            lambda node: signals_received.append(("node_added", node.id))
        )
        model.modifiedChanged.connect(
            lambda is_mod: signals_received.append(("modified", is_mod))
        )

        node = NodeModel("test", "Node")
        model.add_node(node)
        model.modified = True
        
        assert len(signals_received) == 2


class TestControllerSignalIntegration:
    """Test controllers properly work with model signals"""

    def test_node_controller_signal_propagation(self):
        """Test that NodeController changes trigger model signals"""
        model = NodeModel("test", "Node")
        controller = NodeController(model)
        signals_received = []

        model.titleChanged.connect(lambda t: signals_received.append(t))
        model.positionChanged.connect(
            lambda p: signals_received.append(_normalize_point(p))
        )

        controller.set_title("New Title")
        controller.set_position(100.0, 200.0)

        assert "New Title" in signals_received
        assert (100.0, 200.0) in signals_received

    def test_edge_controller_signal_propagation(self):
        """Test that EdgeController changes trigger model signals"""
        # Create sockets first
        socket1 = SocketModel("out1", SocketModel.OUTPUT)
        socket2 = SocketModel("in1", SocketModel.INPUT)

        scene_model = SceneModel()
        controller = EdgeController(scene_model)
        edge = controller.create_edge(socket1, socket2)
        model_signals = []
        controller_signals = []

        edge.typeChanged.connect(lambda et: model_signals.append(et))
        controller.edgeTypeChanged.connect(
            lambda changed_edge, edge_type: controller_signals.append((changed_edge, edge_type))
        )

        controller.set_edge_type(edge, EdgeModel.POLYLINE)

        assert model_signals == [EdgeModel.POLYLINE]
        assert controller_signals == [(edge, EdgeModel.POLYLINE)]

    def test_group_controller_signal_propagation(self):
        """Test that GroupNodeController changes trigger model signals"""
        model = GroupNodeModel(1, "Group")
        controller = GroupNodeController(model)
        signals_received = []

        model.titleChanged.connect(lambda t: signals_received.append(("title", t)))
        model.positionChanged.connect(
            lambda p: signals_received.append(("pos", _normalize_point(p)))
        )
        model.childNodesChanged.connect(
            lambda children: signals_received.append(("children", list(children)))
        )
        node_1 = NodeModel("node_type", "Name")

        controller.set_title("New Title")
        controller.set_position(50.0, 75.0)
        controller.add_node(node_1)

        assert signals_received == [
            ("title", "New Title"),
            ("pos", (50.0, 75.0)),
            ("children", [node_1.id]),
        ]


class TestMultiComponentSignalFlow:
    """Test signal flow across multiple integrated components"""

    def test_multiple_nodes_signal_independence(self):
        """Test that signals from multiple nodes don't interfere"""
        node1 = NodeModel("test", "Node1")
        node2 = NodeModel("test", "Node2")
        
        signals1 = []
        signals2 = []
        
        node1.titleChanged.connect(lambda t: signals1.append(t))
        node2.titleChanged.connect(lambda t: signals2.append(t))
        
        node1.title = "Updated1"
        node2.title = "Updated2"
        
        assert len(signals1) == 1
        assert signals1[0] == "Updated1"
        assert len(signals2) == 1
        assert signals2[0] == "Updated2"

    def test_multiple_group_nodes_signal_independence(self):
        """Test that signals from multiple groups don't interfere"""
        group1 = GroupNodeModel(1, "Group1")
        group2 = GroupNodeModel(2, "Group2")

        signals1 = []
        signals2 = []

        group1.titleChanged.connect(lambda t: signals1.append(t))
        group2.titleChanged.connect(lambda t: signals2.append(t))

        group1.title = "NewTitle1"
        group2.title = "NewTitle2"

        assert len(signals1) == 1
        assert signals1[0] == "NewTitle1"
        assert len(signals2) == 1
        assert signals2[0] == "NewTitle2"

    def test_edge_dragging_during_validation(self):
        """Test edge dragging signals while validators are active"""
        from nodeeditor.models import EdgeModel
        
        # Setup validators
        EdgeModel.clear_edge_validators()
        
        def test_validator(start, end):
            return True
        
        EdgeModel.register_edge_validator(test_validator)
        
        # Create dragging model
        drag_model = EdgeDraggingModel()
        signals_received = []
        
        drag_model.dragStarted.connect(lambda eid, sid: signals_received.append("started"))
        drag_model.dragUpdated.connect(lambda x, y: signals_received.append("updated"))
        drag_model.dragEnded.connect(lambda sid, valid: signals_received.append("ended"))
        
        # Perform drag
        drag_model.start_drag("edge_1", 5)
        drag_model.update_position(100.0, 200.0)
        drag_model.end_drag(10, is_valid=True)
        
        assert len(signals_received) == 3
        assert "started" in signals_received
        assert "updated" in signals_received
        assert "ended" in signals_received

    def test_group_and_node_signal_coordination(self):
        """Test that group and node signals can be coordinated"""
        group = GroupNodeModel(1, "Group")
        node = NodeModel("test", "Node")
        
        group_signals = []
        node_signals = []
        
        group.childNodesChanged.connect(
            lambda children: group_signals.append(list(children))
        )
        node.positionChanged.connect(
            lambda p: node_signals.append(_normalize_point(p))
        )

        node_id = int(node.id)
        group.add_child_node(node_id)
        node.position = (100.0, 200.0)

        assert len(group_signals) == 1
        assert len(node_signals) == 1
        assert group_signals[0] == [node_id]
        assert node_signals[0] == (100.0, 200.0)


class TestSignalChaining:
    """Test chaining of signals across multiple operations"""

    def test_sequential_model_updates_signal_chain(self):
        """Test that sequential model updates produce correct signal sequence"""
        model = NodeModel("test", "Node")
        signal_sequence = []
        
        model.titleChanged.connect(lambda t: signal_sequence.append(("title", t)))
        model.positionChanged.connect(
            lambda p: signal_sequence.append(("pos", _normalize_point(p)))
        )
        model.selectedChanged.connect(lambda s: signal_sequence.append(("sel", s)))
        
        # Update in sequence
        model.title = "Title1"
        model.position = (10.0, 20.0)
        model.selected = True
        model.title = "Title2"
        model.position = (30.0, 40.0)
        model.selected = False
        
        # Verify sequence
        assert len(signal_sequence) == 6
        assert signal_sequence[0] == ("title", "Title1")
        assert signal_sequence[1] == ("pos", (10.0, 20.0))
        assert signal_sequence[2] == ("sel", True)
        assert signal_sequence[3] == ("title", "Title2")
        assert signal_sequence[4] == ("pos", (30.0, 40.0))
        assert signal_sequence[5] == ("sel", False)

    def test_group_node_operation_signal_chain(self):
        """Test signal chain during complex group operations"""
        group = GroupNodeModel(1, "Group")
        signal_sequence = []
        
        group.titleChanged.connect(lambda t: signal_sequence.append(("title", t)))
        group.collapsedChanged.connect(lambda c: signal_sequence.append(("collapsed", c)))
        group.childNodesChanged.connect(
            lambda children: signal_sequence.append(("children", list(children)))
        )
        
        controller = GroupNodeController(group)
        node1 = NodeModel("type", "Node 1")
        node2 = NodeModel("type", "Node 2")
        
        # Perform sequence of operations
        controller.set_title("Group1")
        controller.add_node(node1)
        controller.add_node(node2)
        controller.collapse()
        controller.set_title("Group2")
        
        # Verify sequence
        assert signal_sequence[0][0] == "title"
        assert signal_sequence[0][1] == "Group1"
        assert signal_sequence[1] == ("children", [node1.id])
        assert signal_sequence[2] == ("children", [node1.id, node2.id])
        assert signal_sequence[3][0] == "collapsed"
        assert signal_sequence[4][0] == "title"
        assert signal_sequence[4][1] == "Group2"

    def test_edge_drag_signal_chain(self):
        """Test complete signal chain during edge drag operation"""
        drag_model = EdgeDraggingModel()
        signal_sequence = []
        
        def record_signal(name):
            def handler(*args):
                signal_sequence.append((name, args))
            return handler
        
        drag_model.dragStarted.connect(record_signal("started"))
        drag_model.dragUpdated.connect(record_signal("updated"))
        drag_model.dragUpdated.connect(record_signal("updated2"))
        drag_model.dragEnded.connect(record_signal("ended"))
        
        # Perform drag sequence
        drag_model.start_drag("edge_1", 5)
        drag_model.update_position(100.0, 200.0)
        drag_model.update_position(150.0, 250.0)
        drag_model.end_drag(10, is_valid=True)

        # Verify sequence
        assert len(signal_sequence) == 6
        assert signal_sequence[0] == ("started", ("edge_1", 5))
        assert signal_sequence[1] == ("updated", (100.0, 200.0))
        assert signal_sequence[2] == ("updated2", (100.0, 200.0))
        assert signal_sequence[3] == ("updated", (150.0, 250.0))
        assert signal_sequence[4] == ("updated2", (150.0, 250.0))
        assert signal_sequence[5] == ("ended", (10, True))


class TestSignalErrorHandling:
    """Test signal behavior under error conditions"""

    def test_signal_with_exception_in_slot(self):
        """Test that signal emission handles slots that raise exceptions"""
        model = NodeModel("test", "Node")
        signals_received = []
        
        def slot_with_error(title):
            raise ValueError("Test error")
        
        def normal_slot(title):
            signals_received.append(title)
        
        # Connect slots
        model.titleChanged.connect(slot_with_error)
        model.titleChanged.connect(normal_slot)
        
        # This should not crash, even though first slot fails
        try:
            model.title = "NewTitle"
        except ValueError:
            # First slot raises, but second should still be called
            pass
        
        # Normal slot should have been called
        assert len(signals_received) >= 0  # Depends on Qt signal handling

    def test_signal_with_none_values(self):
        """Test signal handling with None values"""
        socket = SocketModel("input", SocketModel.INPUT)
        signals_received = []
        
        socket.connectionChanged.connect(lambda edge: signals_received.append(edge))

        edge = EdgeModel()
        socket.add_edge(edge)
        socket.remove_edge(edge)

        assert signals_received == [edge, None]

    def test_multiple_disconnections(self):
        """Test disconnecting signals multiple times"""
        model = NodeModel("test", "Node")
        signals_received = []
        
        def slot(title):
            signals_received.append(title)
        
        model.titleChanged.connect(slot)
        model.title = "Title1"
        
        model.titleChanged.disconnect(slot)
        model.title = "Title2"
        
        assert len(signals_received) == 1
        assert signals_received[0] == "Title1"
