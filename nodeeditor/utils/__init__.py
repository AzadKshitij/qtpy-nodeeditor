"""
Utility modules for data conversion, comparison, validation, and other helper functions.

Submodules:
    data_conversion: Convert between Qt types and Python types
    data_comparison: Compare Qt types and complex data structures with tolerance
    node_edge_validators: Edge connection validation functions
    node_edge_snapping: Edge snapping and routing functionality
    node_edge_intersect: Edge intersection detection
    node_edge_rerouting: Dynamic edge path recalculation
    node_group_utils: Group node utility functions
    utils: General utility functions for Qt and UI
"""

from .data_conversion import (
    qpointf_to_tuple,
    tuple_to_qpointf,
    qsizef_to_tuple,
    tuple_to_qsizef,
    qrectf_to_dict,
    dict_to_qrectf,
    qcolor_to_hex,
    hex_to_qcolor,
    normalize_point,
    normalize_size,
    normalize_rect,
)

from .data_comparison import (
    floats_equal,
    tuples_equal,
    qpointf_equal,
    qsizef_equal,
    qrectf_equal,
    qcolor_equal,
    dict_equal,
    dicts_contain_equal_values,
    any_values_equal,
    DEFAULT_FLOAT_TOLERANCE,
)

from .node_edge_validators import (
    edge_validator_debug,
    edge_cannot_connect_two_outputs_or_two_inputs,
    edge_cannot_connect_input_and_output_of_same_node,
    edge_cannot_connect_input_and_output_of_different_type,
)

from .utils import (
    loadStylesheet,
    loadStylesheets,
    isCTRLPressed,
    isSHIFTPressed,
    isALTPressed,
)

__all__ = [
    # Data conversion
    'qpointf_to_tuple',
    'tuple_to_qpointf',
    'qsizef_to_tuple',
    'tuple_to_qsizef',
    'qrectf_to_dict',
    'dict_to_qrectf',
    'qcolor_to_hex',
    'hex_to_qcolor',
    'normalize_point',
    'normalize_size',
    'normalize_rect',
    # Data comparison
    'floats_equal',
    'tuples_equal',
    'qpointf_equal',
    'qsizef_equal',
    'qrectf_equal',
    'qcolor_equal',
    'dict_equal',
    'dicts_contain_equal_values',
    'any_values_equal',
    'DEFAULT_FLOAT_TOLERANCE',
    # Edge validators
    'edge_validator_debug',
    'edge_cannot_connect_two_outputs_or_two_inputs',
    'edge_cannot_connect_input_and_output_of_same_node',
    'edge_cannot_connect_input_and_output_of_different_type',
    # General utilities
    'loadStylesheet',
    'loadStylesheets',
    'isCTRLPressed',
    'isSHIFTPressed',
    'isALTPressed',
]
