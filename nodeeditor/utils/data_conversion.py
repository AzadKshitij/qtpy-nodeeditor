"""
Data Type Conversion Utilities

Provides utilities for converting between Qt types and Python native types,
particularly for serialization and API compatibility.
"""

from typing import Tuple, Dict, Any, Union, List, Optional
from qtpy.QtCore import QPointF, QSizeF, QRectF, QPoint, QSize, QRect
from qtpy.QtGui import QColor


def qpointf_to_tuple(point: Union[QPointF, Tuple[float, float]]) -> Tuple[float, float]:
    """
    Convert QPointF to (x, y) tuple.

    Args:
        point: QPointF or tuple to convert

    Returns:
        Tuple of (x, y) as floats
    """
    if isinstance(point, QPointF):
        return (float(point.x()), float(point.y()))
    if isinstance(point, (tuple, list)) and len(point) == 2:
        return (float(point[0]), float(point[1]))
    raise TypeError(f"Expected QPointF or tuple, got {type(point)}")


def tuple_to_qpointf(data: Tuple[float, float]) -> QPointF:
    """
    Convert (x, y) tuple to QPointF.

    Args:
        data: Tuple of (x, y)

    Returns:
        QPointF instance
    """
    if not isinstance(data, (tuple, list)) or len(data) != 2:
        raise ValueError(f"Expected tuple of 2 elements, got {data}")
    return QPointF(float(data[0]), float(data[1]))


def qsizef_to_tuple(size: Union[QSizeF, Tuple[float, float]]) -> Tuple[float, float]:
    """
    Convert QSizeF to (width, height) tuple.

    Args:
        size: QSizeF or tuple to convert

    Returns:
        Tuple of (width, height) as floats
    """
    if isinstance(size, QSizeF):
        return (float(size.width()), float(size.height()))
    if isinstance(size, (tuple, list)) and len(size) == 2:
        return (float(size[0]), float(size[1]))
    raise TypeError(f"Expected QSizeF or tuple, got {type(size)}")


def tuple_to_qsizef(data: Tuple[float, float]) -> QSizeF:
    """
    Convert (width, height) tuple to QSizeF.

    Args:
        data: Tuple of (width, height)

    Returns:
        QSizeF instance
    """
    if not isinstance(data, (tuple, list)) or len(data) != 2:
        raise ValueError(f"Expected tuple of 2 elements, got {data}")
    return QSizeF(float(data[0]), float(data[1]))


def qrectf_to_dict(rect: Union[QRectF, Dict[str, float]]) -> Dict[str, float]:
    """
    Convert QRectF to dictionary with x, y, width, height keys.

    Args:
        rect: QRectF or dict to convert

    Returns:
        Dictionary with keys: x, y, width, height
    """
    if isinstance(rect, QRectF):
        return {
            'x': float(rect.x()),
            'y': float(rect.y()),
            'width': float(rect.width()),
            'height': float(rect.height())
        }
    if isinstance(rect, dict):
        required_keys = {'x', 'y', 'width', 'height'}
        if not required_keys.issubset(rect.keys()):
            raise ValueError(f"Dict must contain keys {required_keys}")
        return {k: float(v) for k, v in rect.items() if k in required_keys}
    raise TypeError(f"Expected QRectF or dict, got {type(rect)}")


def dict_to_qrectf(data: Dict[str, float]) -> QRectF:
    """
    Convert dictionary to QRectF.

    Args:
        data: Dictionary with x, y, width, height keys

    Returns:
        QRectF instance
    """
    if not isinstance(data, dict):
        raise TypeError(f"Expected dict, got {type(data)}")
    required_keys = {'x', 'y', 'width', 'height'}
    if not required_keys.issubset(data.keys()):
        raise ValueError(f"Dict must contain keys {required_keys}, got {set(data.keys())}")
    return QRectF(float(data['x']), float(data['y']), 
                  float(data['width']), float(data['height']))


def qcolor_to_hex(color: Union[QColor, str]) -> str:
    """
    Convert QColor to hex color string (#RRGGBB or #AARRGGBB).

    Args:
        color: QColor or hex string to convert

    Returns:
        Hex color string
    """
    if isinstance(color, QColor):
        if color.alpha() != 255:
            return color.name(QColor.HexArgb)
        return color.name()
    if isinstance(color, str):
        if not (color.startswith('#') and len(color) in [7, 9]):
            raise ValueError(f"Invalid hex color: {color}")
        return color
    raise TypeError(f"Expected QColor or str, got {type(color)}")


def hex_to_qcolor(hex_str: str) -> QColor:
    """
    Convert hex color string to QColor.

    Args:
        hex_str: Hex color string (#RRGGBB or #AARRGGBB)

    Returns:
        QColor instance
    """
    if not isinstance(hex_str, str):
        raise TypeError(f"Expected str, got {type(hex_str)}")
    if not (hex_str.startswith('#') and len(hex_str) in [7, 9]):
        raise ValueError(f"Invalid hex color: {hex_str}")
    color = QColor(hex_str)
    if not color.isValid():
        raise ValueError(f"Invalid hex color: {hex_str}")
    return color


def normalize_point(value: Any) -> Tuple[float, float]:
    """
    Normalize any point-like value to (x, y) tuple.

    Args:
        value: QPointF, tuple, or other point-like object

    Returns:
        Tuple of (x, y) as floats
    """
    if isinstance(value, QPointF):
        return (float(value.x()), float(value.y()))
    if isinstance(value, QPoint):
        return (float(value.x()), float(value.y()))
    if isinstance(value, (tuple, list)) and len(value) == 2:
        try:
            return (float(value[0]), float(value[1]))
        except (TypeError, ValueError):
            return tuple(value)
    return value


def normalize_size(value: Any) -> Tuple[float, float]:
    """
    Normalize any size-like value to (width, height) tuple.

    Args:
        value: QSizeF, tuple, or other size-like object

    Returns:
        Tuple of (width, height) as floats
    """
    if isinstance(value, QSizeF):
        return (float(value.width()), float(value.height()))
    if isinstance(value, QSize):
        return (float(value.width()), float(value.height()))
    if isinstance(value, (tuple, list)) and len(value) == 2:
        try:
            return (float(value[0]), float(value[1]))
        except (TypeError, ValueError):
            return tuple(value)
    return value


def normalize_rect(value: Any) -> Dict[str, float]:
    """
    Normalize any rect-like value to dictionary.

    Args:
        value: QRectF, dict, or other rect-like object

    Returns:
        Dictionary with x, y, width, height keys
    """
    if isinstance(value, QRectF):
        return qrectf_to_dict(value)
    if isinstance(value, QRect):
        return {
            'x': float(value.x()),
            'y': float(value.y()),
            'width': float(value.width()),
            'height': float(value.height())
        }
    if isinstance(value, dict):
        return qrectf_to_dict(value)
    return value
