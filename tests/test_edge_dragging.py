"""
Test suite for Edge Dragging MVC integration.

Tests EdgeDraggingModel, EdgeDragging refactored class, and validator integration.
"""

import pytest
from qtpy.QtCore import Qt
from nodeeditor.models import EdgeDraggingModel, EdgeModel
from nodeeditor.utils.node_edge_validators import (
    edge_cannot_connect_two_outputs_or_two_inputs,
    edge_cannot_connect_input_and_output_of_same_node,
    edge_cannot_connect_input_and_output_of_different_type,
)


class TestEdgeDraggingModel:
    """Test cases for EdgeDraggingModel"""

    def test_create_edge_dragging_model(self):
        """Test creating an EdgeDraggingModel"""
        model = EdgeDraggingModel()
        assert not model.is_dragging
        assert model.edge_id is None
        assert model.start_socket_id is None
        assert model.last_position == (0.0, 0.0)

    def test_start_drag(self):
        """Test starting a drag operation"""
        model = EdgeDraggingModel()
        signals_received = []
        
        model.dragStarted.connect(lambda edge_id, socket_id: signals_received.append(("started", edge_id, socket_id)))
        
        model.start_drag("edge_123", 5)
        
        assert model.is_dragging
        assert model.edge_id == "edge_123"
        assert model.start_socket_id == 5
        assert len(signals_received) == 1
        assert signals_received[0] == ("started", "edge_123", 5)

    def test_update_position(self):
        """Test updating drag position"""
        model = EdgeDraggingModel()
        signals_received = []
        
        model.dragUpdated.connect(lambda x, y: signals_received.append(("updated", x, y)))
        
        model.start_drag("edge_123", 5)
        model.update_position(100.0, 200.0)
        
        assert model.last_position == (100.0, 200.0)
        assert len(signals_received) == 1
        assert signals_received[0] == ("updated", 100.0, 200.0)

    def test_end_drag(self):
        """Test ending a drag operation"""
        model = EdgeDraggingModel()
        signals_received = []
        
        model.dragEnded.connect(lambda socket_id, is_valid: signals_received.append(("ended", socket_id, is_valid)))
        
        model.start_drag("edge_123", 5)
        model.end_drag(10, is_valid=True)
        
        assert not model.is_dragging
        assert model.edge_id is None
        assert model.start_socket_id is None
        assert len(signals_received) == 1
        assert signals_received[0] == ("ended", 10, True)

    def test_end_drag_invalid(self):
        """Test ending drag with invalid connection"""
        model = EdgeDraggingModel()
        signals_received = []
        
        model.dragEnded.connect(lambda socket_id, is_valid: signals_received.append(("ended", socket_id, is_valid)))
        
        model.start_drag("edge_123", 5)
        model.end_drag(10, is_valid=False)
        
        assert not model.is_dragging
        assert len(signals_received) == 1
        assert signals_received[0] == ("ended", 10, False)

    def test_cancel_drag(self):
        """Test cancelling a drag operation"""
        model = EdgeDraggingModel()
        signals_received = []
        
        model.dragCancelled.connect(lambda: signals_received.append("cancelled"))
        
        model.start_drag("edge_123", 5)
        model.cancel_drag()
        
        assert not model.is_dragging
        assert model.edge_id is None
        assert model.start_socket_id is None
        assert len(signals_received) == 1
        assert signals_received[0] == "cancelled"

    def test_cancel_drag_when_not_dragging(self):
        """Test cancelling when not actively dragging"""
        model = EdgeDraggingModel()
        signals_received = []
        
        model.dragCancelled.connect(lambda: signals_received.append("cancelled"))
        
        # Cancel without starting drag
        model.cancel_drag()
        
        assert not model.is_dragging
        # Signal should not be emitted if already not dragging
        assert len(signals_received) == 0

    def test_end_drag_when_not_dragging(self):
        """Test ending drag when not actively dragging"""
        model = EdgeDraggingModel()
        signals_received = []
        
        model.dragEnded.connect(lambda socket_id, is_valid: signals_received.append(("ended", socket_id, is_valid)))
        
        # End drag without starting
        model.end_drag(10, is_valid=True)
        
        # Signal should not be emitted if not dragging
        assert len(signals_received) == 0


class TestEdgeModelValidators:
    """Test cases for EdgeModel validator registration and validation"""

    def setup_method(self):
        """Clear validators before each test"""
        EdgeModel.clear_edge_validators()

    def test_register_validator(self):
        """Test registering a validator"""
        def dummy_validator(start, end):
            return True
        
        EdgeModel.register_edge_validator(dummy_validator)
        validators = EdgeModel.get_edge_validators()
        
        assert len(validators) == 1
        assert dummy_validator in validators

    def test_unregister_validator(self):
        """Test unregistering a validator"""
        def dummy_validator(start, end):
            return True
        
        EdgeModel.register_edge_validator(dummy_validator)
        EdgeModel.unregister_edge_validator(dummy_validator)
        validators = EdgeModel.get_edge_validators()
        
        assert len(validators) == 0
        assert dummy_validator not in validators

    def test_no_duplicate_validators(self):
        """Test that validators are not registered twice"""
        def dummy_validator(start, end):
            return True
        
        EdgeModel.register_edge_validator(dummy_validator)
        EdgeModel.register_edge_validator(dummy_validator)
        validators = EdgeModel.get_edge_validators()
        
        assert len(validators) == 1

    def test_clear_validators(self):
        """Test clearing all validators"""
        def validator1(start, end):
            return True
        
        def validator2(start, end):
            return True
        
        EdgeModel.register_edge_validator(validator1)
        EdgeModel.register_edge_validator(validator2)
        
        validators = EdgeModel.get_edge_validators()
        assert len(validators) == 2
        
        EdgeModel.clear_edge_validators()
        validators = EdgeModel.get_edge_validators()
        assert len(validators) == 0

    def test_validate_socket_connection_all_pass(self):
        """Test validation when all validators pass"""
        def validator1(start, end):
            return True
        
        def validator2(start, end):
            return True
        
        EdgeModel.register_edge_validator(validator1)
        EdgeModel.register_edge_validator(validator2)
        
        # Create mock sockets (objects with required attributes)
        class MockSocket:
            def __init__(self, is_input, socket_type, node_id):
                self.is_input = is_input
                self.socket_type = socket_type
                self.node_id = node_id
        
        start_socket = MockSocket(is_input=False, socket_type=1, node_id=1)
        end_socket = MockSocket(is_input=True, socket_type=1, node_id=2)
        
        result = EdgeModel.validate_socket_connection(start_socket, end_socket)
        assert result is True

    def test_validate_socket_connection_one_fails(self):
        """Test validation when one validator fails"""
        def validator_pass(start, end):
            return True
        
        def validator_fail(start, end):
            return False
        
        EdgeModel.register_edge_validator(validator_pass)
        EdgeModel.register_edge_validator(validator_fail)
        
        class MockSocket:
            def __init__(self, is_input, socket_type, node_id):
                self.is_input = is_input
                self.socket_type = socket_type
                self.node_id = node_id
        
        start_socket = MockSocket(is_input=False, socket_type=1, node_id=1)
        end_socket = MockSocket(is_input=True, socket_type=1, node_id=2)
        
        result = EdgeModel.validate_socket_connection(start_socket, end_socket)
        assert result is False

    def test_validate_socket_connection_no_validators(self):
        """Test validation with no validators (should always pass)"""
        class MockSocket:
            def __init__(self, is_input, socket_type, node_id):
                self.is_input = is_input
                self.socket_type = socket_type
                self.node_id = node_id
        
        start_socket = MockSocket(is_input=False, socket_type=1, node_id=1)
        end_socket = MockSocket(is_input=True, socket_type=1, node_id=2)
        
        result = EdgeModel.validate_socket_connection(start_socket, end_socket)
        assert result is True

    def test_two_outputs_validator(self):
        """Test the two outputs/inputs validator"""
        EdgeModel.clear_edge_validators()
        EdgeModel.register_edge_validator(edge_cannot_connect_two_outputs_or_two_inputs)
        
        class MockSocket:
            def __init__(self, is_input, socket_type, node_id):
                self.is_input = is_input
                self.is_output = not is_input
                self.socket_type = socket_type
                self.node_id = node_id
        
        # Two outputs should fail
        output1 = MockSocket(is_input=False, socket_type=1, node_id=1)
        output2 = MockSocket(is_input=False, socket_type=1, node_id=2)
        
        result = EdgeModel.validate_socket_connection(output1, output2)
        assert result is False
        
        # Output to input should pass
        input_socket = MockSocket(is_input=True, socket_type=1, node_id=3)
        result = EdgeModel.validate_socket_connection(output1, input_socket)
        assert result is True

    def test_same_node_validator(self):
        """Test the same node validator"""
        EdgeModel.clear_edge_validators()
        EdgeModel.register_edge_validator(edge_cannot_connect_input_and_output_of_same_node)
        
        class MockNode:
            def __init__(self, node_id):
                self.node_id = node_id
        
        class MockSocket:
            def __init__(self, is_input, node):
                self.is_input = is_input
                self.is_output = not is_input
                self.node = node
        
        # Same node should fail - use the SAME MockNode instance
        node1 = MockNode(1)
        socket1 = MockSocket(is_input=False, node=node1)
        socket2 = MockSocket(is_input=True, node=node1)
        
        result = EdgeModel.validate_socket_connection(socket1, socket2)
        assert result is False
        
        # Different nodes should pass
        node2 = MockNode(2)
        socket3 = MockSocket(is_input=True, node=node2)
        result = EdgeModel.validate_socket_connection(socket1, socket3)
        assert result is True

    def test_different_type_validator(self):
        """Test the different socket type validator"""
        EdgeModel.clear_edge_validators()
        EdgeModel.register_edge_validator(edge_cannot_connect_input_and_output_of_different_type)
        
        class MockSocket:
            def __init__(self, is_input, socket_type):
                self.is_input = is_input
                self.is_output = not is_input
                self.socket_type = socket_type
        
        # Different types should fail
        socket1 = MockSocket(is_input=False, socket_type=1)
        socket2 = MockSocket(is_input=True, socket_type=2)
        
        result = EdgeModel.validate_socket_connection(socket1, socket2)
        assert result is False
        
        # Same types should pass
        socket3 = MockSocket(is_input=True, socket_type=1)
        result = EdgeModel.validate_socket_connection(socket1, socket3)
        assert result is True


class TestDefaultValidatorRegistration:
    """Test that default validators are auto-registered on import"""

    def test_default_validators_registered(self):
        """Test that importing edge_validator_registration registers validators"""
        # Re-import to trigger registration
        import importlib
        import nodeeditor.edge_validator_registration as evr
        importlib.reload(evr)
        
        validators = EdgeModel.get_edge_validators()
        # Should have registered 4 default validators
        assert len(validators) >= 4

    def test_validator_stack_order(self):
        """Test that validators are called in order"""
        EdgeModel.clear_edge_validators()
        call_order = []
        
        def validator1(start, end):
            call_order.append(1)
            return True
        
        def validator2(start, end):
            call_order.append(2)
            return True
        
        def validator3(start, end):
            call_order.append(3)
            return True
        
        EdgeModel.register_edge_validator(validator1)
        EdgeModel.register_edge_validator(validator2)
        EdgeModel.register_edge_validator(validator3)
        
        class MockSocket:
            def __init__(self):
                self.is_input = True
                self.socket_type = 1
        
        EdgeModel.validate_socket_connection(MockSocket(), MockSocket())
        
        assert call_order == [1, 2, 3]
