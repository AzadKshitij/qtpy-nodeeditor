"""Cost of one primitive operation, in microseconds.

These are the numbers that decide whether a compiler could help: a Python
call versus a Qt call across the sip/shiboken boundary. They are measured
with ``timeit`` so each one is independent of the scene.
"""

import timeit

from typing import Dict

from qtpy.QtCore import QLine, QPointF, QRectF
from qtpy.QtGui import QColor, QPainterPath


def _us(function, number: int = 20000, repeat: int = 5) -> float:
    return min(timeit.repeat(function, number=number, repeat=repeat)) / number * 1e6


def run_micro() -> Dict[str, float]:
    composite = QPainterPath()
    composite.addRoundedRect(0, 0, 180, 24, 10, 10)
    composite.addRect(0, 14, 10, 10)
    composite.addRect(170, 14, 10, 10)

    def add_rounded():
        path = QPainterPath()
        path.addRoundedRect(0, 0, 180, 24, 10, 10)
        return path

    def cubic():
        path = QPainterPath(QPointF(0, 0))
        path.cubicTo(QPointF(1, 0), QPointF(2, 3), QPointF(4, 5))
        return path

    return {
        "python_call": _us(lambda: None),
        "QPointF": _us(lambda: QPointF(1.0, 2.0)),
        "QRectF": _us(lambda: QRectF(0, 0, 1, 1)),
        "QLine": _us(lambda: QLine(0, 0, 100, 100)),
        "QColor": _us(lambda: QColor(10, 20, 30)),
        "QPainterPath": _us(lambda: QPainterPath()),
        "path.addRoundedRect": _us(add_rounded),
        "path.simplified": _us(lambda: composite.simplified()),
        "path.cubicTo": _us(cubic),
        "math.sqrt": _us(lambda: __import__("math").sqrt(3.0)),
    }
