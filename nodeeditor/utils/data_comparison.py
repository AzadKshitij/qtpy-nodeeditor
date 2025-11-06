"""
Data Type Comparison Utilities

Provides utilities for comparing complex types, particularly Qt types,
with tolerance for floating-point comparisons.
"""

from typing import Any, Tuple, Dict, Union
from qtpy.QtCore import QPointF, QSizeF, QRectF, QPoint, QSize, QRect
from qtpy.QtGui import QColor


DEFAULT_FLOAT_TOLERANCE = 1e-9


def floats_equal(a: float, b: float, tolerance: float = DEFAULT_FLOAT_TOLERANCE) -> bool:
    """
    Compare two floats with tolerance.

    Args:
        a: First float value
        b: Second float value
        tolerance: Maximum difference for equality

    Returns:
        True if values are equal within tolerance
    """
    return abs(float(a) - float(b)) <= tolerance


def tuples_equal(a: Tuple[float, float], b: Tuple[float, float], 
                tolerance: float = DEFAULT_FLOAT_TOLERANCE) -> bool:
    """
    Compare two float tuples with tolerance.

    Args:
        a: First tuple
        b: Second tuple
        tolerance: Maximum difference for equality

    Returns:
        True if tuples are equal within tolerance
    """
    if len(a) != len(b):
        return False
    return all(floats_equal(x, y, tolerance) for x, y in zip(a, b))


def qpointf_equal(a: QPointF, b: QPointF, 
                 tolerance: float = DEFAULT_FLOAT_TOLERANCE) -> bool:
    """
    Compare two QPointF objects with tolerance.

    Args:
        a: First QPointF
        b: Second QPointF
        tolerance: Maximum difference for equality

    Returns:
        True if points are equal within tolerance
    """
    return (floats_equal(a.x(), b.x(), tolerance) and 
            floats_equal(a.y(), b.y(), tolerance))


def qsizef_equal(a: QSizeF, b: QSizeF, 
                tolerance: float = DEFAULT_FLOAT_TOLERANCE) -> bool:
    """
    Compare two QSizeF objects with tolerance.

    Args:
        a: First QSizeF
        b: Second QSizeF
        tolerance: Maximum difference for equality

    Returns:
        True if sizes are equal within tolerance
    """
    return (floats_equal(a.width(), b.width(), tolerance) and 
            floats_equal(a.height(), b.height(), tolerance))


def qrectf_equal(a: QRectF, b: QRectF, 
                tolerance: float = DEFAULT_FLOAT_TOLERANCE) -> bool:
    """
    Compare two QRectF objects with tolerance.

    Args:
        a: First QRectF
        b: Second QRectF
        tolerance: Maximum difference for equality

    Returns:
        True if rectangles are equal within tolerance
    """
    return (floats_equal(a.x(), b.x(), tolerance) and 
            floats_equal(a.y(), b.y(), tolerance) and
            floats_equal(a.width(), b.width(), tolerance) and
            floats_equal(a.height(), b.height(), tolerance))


def qcolor_equal(a: QColor, b: QColor) -> bool:
    """
    Compare two QColor objects.

    Args:
        a: First QColor
        b: Second QColor

    Returns:
        True if colors are equal
    """
    return a == b


def dict_equal(a: Dict[str, Any], b: Dict[str, Any], 
              tolerance: float = DEFAULT_FLOAT_TOLERANCE) -> bool:
    """
    Deep compare two dictionaries with tolerance for floats.

    Args:
        a: First dictionary
        b: Second dictionary
        tolerance: Tolerance for float comparisons

    Returns:
        True if dictionaries are equal
    """
    if set(a.keys()) != set(b.keys()):
        return False
    
    for key in a.keys():
        val_a = a[key]
        val_b = b[key]
        
        if isinstance(val_a, float) and isinstance(val_b, float):
            if not floats_equal(val_a, val_b, tolerance):
                return False
        elif isinstance(val_a, dict) and isinstance(val_b, dict):
            if not dict_equal(val_a, val_b, tolerance):
                return False
        elif isinstance(val_a, (list, tuple)) and isinstance(val_b, (list, tuple)):
            if len(val_a) != len(val_b):
                return False
            for x, y in zip(val_a, val_b):
                if isinstance(x, float) and isinstance(y, float):
                    if not floats_equal(x, y, tolerance):
                        return False
                elif x != y:
                    return False
        elif val_a != val_b:
            return False
    
    return True


def dicts_contain_equal_values(a: Dict[str, Any], b: Dict[str, Any],
                              tolerance: float = DEFAULT_FLOAT_TOLERANCE) -> bool:
    """
    Check if dict b contains all key-value pairs from dict a (subset comparison).

    Args:
        a: Subset dictionary
        b: Superset dictionary
        tolerance: Tolerance for float comparisons

    Returns:
        True if all items from a are equal in b
    """
    for key in a.keys():
        if key not in b:
            return False
        val_a = a[key]
        val_b = b[key]
        
        if isinstance(val_a, float) and isinstance(val_b, float):
            if not floats_equal(val_a, val_b, tolerance):
                return False
        elif isinstance(val_a, dict) and isinstance(val_b, dict):
            if not dicts_contain_equal_values(val_a, val_b, tolerance):
                return False
        elif val_a != val_b:
            return False
    
    return True


def any_values_equal(values: list[Any], compare_to: Any, 
                    tolerance: float = DEFAULT_FLOAT_TOLERANCE) -> bool:
    """
    Check if any value in a list equals the compare_to value.

    Args:
        values: List of values to check
        compare_to: Value to compare against
        tolerance: Tolerance for float comparisons

    Returns:
        True if any value equals compare_to
    """
    for value in values:
        if isinstance(value, float) and isinstance(compare_to, float):
            if floats_equal(value, compare_to, tolerance):
                return True
        elif isinstance(value, QPointF) and isinstance(compare_to, QPointF):
            if qpointf_equal(value, compare_to, tolerance):
                return True
        elif isinstance(value, dict) and isinstance(compare_to, dict):
            if dict_equal(value, compare_to, tolerance):
                return True
        elif value == compare_to:
            return True
    
    return False
