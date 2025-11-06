"""
MVC Calculator Base Models

Provides base model classes for calculator nodes that extend the core MVC models
from nodeeditor. These models represent the data and state for calculator nodes.
"""

from typing import List, Optional, Any, Dict
from nodeeditor.models import NodeModel, SocketModel


class CalcNodeModel(NodeModel):
    """
    Base model for calculator nodes in the MVC architecture.

    Extends NodeModel with calculator-specific properties like operation codes,
    input/output configuration, and computation values.

    Attributes:
        op_code: Integer operation code identifying the node type
        op_title: Display title for the node
        values: List of computed values (one per output socket)
        icon: Path to the node's icon
    """

    op_code: int = 0
    op_title: str = "Undefined"
    icon: str = ""

    def __init__(
        self,
        node_type: str,
        title: str = "Node",
        node_id: Optional[int] = None,
    ) -> None:
        """
        Initialize a CalcNodeModel.

        Args:
            node_type: Type identifier (e.g., "calc_input", "calc_add")
            title: Display name
            node_id: Optional unique identifier
        """
        super().__init__(node_type, title, node_id)
        self.values: List[Any] = []


class CalcInputNodeModel(CalcNodeModel):
    """
    Model for input nodes in the calculator.

    Stores an input value that can be edited by the user.
    """

    def __init__(
        self,
        node_id: Optional[int] = None,
        initial_value: int = 1,
    ) -> None:
        """
        Initialize an input node model.

        Args:
            node_id: Optional unique identifier
            initial_value: Initial numeric value
        """
        super().__init__("calc_input", "Input", node_id)
        self.set_property("value", initial_value)


class CalcOutputNodeModel(CalcNodeModel):
    """
    Model for output nodes in the calculator.

    Displays computed values from connected inputs.
    """

    def __init__(self, node_id: Optional[int] = None) -> None:
        """
        Initialize an output node model.

        Args:
            node_id: Optional unique identifier
        """
        super().__init__("calc_output", "Output", node_id)
        self.set_property("display_value", None)


class CalcOperationNodeModel(CalcNodeModel):
    """
    Base model for operation nodes (Add, Sub, Mul, Div, etc.).

    Computes results based on input values.
    """

    def __init__(
        self,
        node_type: str,
        title: str,
        op_code: int,
        node_id: Optional[int] = None,
    ) -> None:
        """
        Initialize an operation node model.

        Args:
            node_type: Type identifier
            title: Display name
            op_code: Operation code
            node_id: Optional unique identifier
        """
        super().__init__(node_type, title, node_id)
        self.op_code = op_code
        self.set_property("result", None)


class CalcAddNodeModel(CalcOperationNodeModel):
    """Model for addition operation node."""

    def __init__(self, node_id: Optional[int] = None) -> None:
        """Initialize an addition node model."""
        super().__init__("calc_add", "Add", 3, node_id)


class CalcSubNodeModel(CalcOperationNodeModel):
    """Model for subtraction operation node."""

    def __init__(self, node_id: Optional[int] = None) -> None:
        """Initialize a subtraction node model."""
        super().__init__("calc_sub", "Subtract", 4, node_id)


class CalcMulNodeModel(CalcOperationNodeModel):
    """Model for multiplication operation node."""

    def __init__(self, node_id: Optional[int] = None) -> None:
        """Initialize a multiplication node model."""
        super().__init__("calc_mul", "Multiply", 5, node_id)


class CalcDivNodeModel(CalcOperationNodeModel):
    """Model for division operation node."""

    def __init__(self, node_id: Optional[int] = None) -> None:
        """Initialize a division node model."""
        super().__init__("calc_div", "Divide", 6, node_id)
