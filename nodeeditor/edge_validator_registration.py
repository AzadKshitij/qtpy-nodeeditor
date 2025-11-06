# -*- coding: utf-8 -*-
"""
Edge Validator Registration Module

This module registers all default edge validators with the EdgeModel.
Import this module to enable edge validation for the entire application.

Example:
    To enable edge validation on application startup:

    .. code-block:: python

        from nodeeditor.edge_validator_registration import register_default_validators
        register_default_validators()

    Or import directly to register:

    .. code-block:: python

        from nodeeditor import edge_validator_registration  # noqa: F401
"""

from nodeeditor.models import EdgeModel
from nodeeditor.utils.node_edge_validators import (
    edge_validator_debug,
    edge_cannot_connect_two_outputs_or_two_inputs,
    edge_cannot_connect_input_and_output_of_same_node,
    edge_cannot_connect_input_and_output_of_different_type,
)


def register_default_validators() -> None:
    """Register all default edge validators with EdgeModel.
    
    This should be called once at application startup to enable
    edge validation for edge creation and dragging operations.
    """
    # Register validation functions in order of precedence
    EdgeModel.register_edge_validator(edge_validator_debug)
    EdgeModel.register_edge_validator(edge_cannot_connect_two_outputs_or_two_inputs)
    EdgeModel.register_edge_validator(edge_cannot_connect_input_and_output_of_same_node)
    EdgeModel.register_edge_validator(edge_cannot_connect_input_and_output_of_different_type)


# Auto-register on module import
register_default_validators()
