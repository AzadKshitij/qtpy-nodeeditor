"""
MVC Calculator Node Controllers

Controllers manage the business logic for calculator nodes, coordinating
between models (data) and views (graphics).
"""

from typing import Optional, Any, Tuple
import logging

from qtpy.QtCore import QObject, Signal, QPointF

from nodeeditor.controllers import NodeController
from nodeeditor.models import SceneModel
from examples.mvc_calculator.models import (
    CalcNodeModel,
    CalcInputNodeModel,
    CalcOutputNodeModel,
    CalcOperationNodeModel,
)

logger = logging.getLogger(__name__)


class CalcNodeController(NodeController):
    """
    Controller for calculator nodes in MVC architecture.

    Extends NodeController with calculator-specific logic like evaluation,
    value propagation, and computation handling.

    Signals:
        valueComputed: Emitted when a node value is computed (node_id, values)
        evaluationError: Emitted when evaluation fails (node_id, error_msg)
    """

    valueComputed = Signal(int, list)  # node_id, values
    evaluationError = Signal(int, str)  # node_id, error_message

    def __init__(self, scene_model: SceneModel, undo_stack: Optional[Any] = None) -> None:
        """
        Initialize the calculator node controller.

        Args:
            scene_model: The scene model containing nodes
            undo_stack: Optional undo stack for command management
        """
        super().__init__(scene_model, undo_stack)

    def evaluate_node(self, node_id: int) -> Optional[list]:
        """
        Evaluate a calculator node and propagate results.

        Args:
            node_id: ID of the node to evaluate

        Returns:
            List of computed values, or None on error
        """
        node = self.scene_model.get_node(node_id)
        if not node:
            logger.error(f"Node {node_id} not found")
            return None

        try:
            if isinstance(node, CalcInputNodeModel):
                values = self._evaluate_input_node(node)
            elif isinstance(node, CalcOutputNodeModel):
                values = self._evaluate_output_node(node)
            elif isinstance(node, CalcOperationNodeModel):
                values = self._evaluate_operation_node(node)
            else:
                logger.warning(f"Unknown node type: {type(node)}")
                return None

            node.values = values or []
            self.valueComputed.emit(node_id, values or [])
            return values

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error evaluating node {node_id}: {error_msg}")
            self.evaluationError.emit(node_id, error_msg)
            return None

    def _evaluate_input_node(self, node: CalcInputNodeModel) -> list:
        """
        Evaluate an input node by returning its stored value.

        Args:
            node: The input node model

        Returns:
            List containing the input value
        """
        value = node.get_property("value", 0)
        return [value]

    def _evaluate_output_node(self, node: CalcOutputNodeModel) -> list:
        """
        Evaluate an output node by getting connected input values.

        Args:
            node: The output node model

        Returns:
            List containing the displayed value
        """
        # In a real implementation, you would traverse edges to get input
        display_value = node.get_property("display_value", None)
        return [display_value] if display_value is not None else [None]

    def _evaluate_operation_node(self, node: CalcOperationNodeModel) -> list:
        """
        Evaluate an operation node by computing based on inputs.

        Args:
            node: The operation node model

        Returns:
            List containing the computed result
        """
        # In a real implementation, you would traverse edges to get input values
        # and perform the appropriate operation
        result = node.get_property("result", None)
        return [result] if result is not None else [None]

    def set_input_value(self, node_id: int, value: int) -> bool:
        """
        Set the value of an input node.

        Args:
            node_id: ID of the input node
            value: New value to set

        Returns:
            True if successful, False otherwise
        """
        node = self.scene_model.get_node(node_id)
        if not isinstance(node, CalcInputNodeModel):
            logger.error(f"Node {node_id} is not an input node")
            return False

        node.set_property("value", value)
        # Propagate evaluation
        self.evaluate_node(node_id)
        return True

    def get_node_result(self, node_id: int) -> Optional[Any]:
        """
        Get the computed result of a node.

        Args:
            node_id: ID of the node

        Returns:
            The computed value, or None if not available
        """
        node = self.scene_model.get_node(node_id)
        if node and node.values:
            return node.values[0]
        return None
