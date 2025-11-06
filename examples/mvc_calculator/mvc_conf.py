"""
MVC Calculator Configuration

Defines all node types and registers them for the calculator application.
This follows the MVC architecture with node type registration pattern.
"""

LISTBOX_MIMETYPE = "application/x-item"

# Node operation codes
OP_NODE_INPUT = 1
OP_NODE_OUTPUT = 2
OP_NODE_ADD = 3
OP_NODE_SUB = 4
OP_NODE_MUL = 5
OP_NODE_DIV = 6
OP_NODE_CHECK = 7

# Registry of available node types
CALC_NODES = {}


class ConfException(Exception):
    """Base exception for configuration errors"""
    pass


class InvalidNodeRegistration(ConfException):
    """Raised when attempting to register a duplicate node type"""
    pass


class OpCodeNotRegistered(ConfException):
    """Raised when attempting to use an unregistered operation code"""
    pass


def register_node_now(op_code, class_reference):
    """
    Register a node class with its operation code.

    Args:
        op_code: Integer operation code
        class_reference: Node class to register

    Raises:
        InvalidNodeRegistration: If operation code is already registered
    """
    if op_code in CALC_NODES:
        raise InvalidNodeRegistration(
            f"Duplicate node registration of '{op_code}'. "
            f"There is already {CALC_NODES[op_code]}"
        )
    CALC_NODES[op_code] = class_reference


def register_node(op_code):
    """
    Decorator for registering node classes.

    Usage:
        @register_node(OP_NODE_ADD)
        class MyNode:
            ...

    Args:
        op_code: Integer operation code

    Returns:
        Decorator function
    """
    def decorator(original_class):
        register_node_now(op_code, original_class)
        return original_class
    return decorator


def get_class_from_opcode(op_code):
    """
    Get the node class for an operation code.

    Args:
        op_code: Integer operation code

    Returns:
        Node class

    Raises:
        OpCodeNotRegistered: If operation code is not registered
    """
    if op_code not in CALC_NODES:
        raise OpCodeNotRegistered(f"OpCode '{op_code}' is not registered")
    return CALC_NODES[op_code]


# Import all node definitions to register them
from examples.mvc_calculator.nodes import *  # noqa: F401, E402
