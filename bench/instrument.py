"""Microsecond timers for the nodeeditor hot paths.

Only Python-level methods are wrapped. Qt's C++ work is timed inclusively by
the Python method that calls it, which is exactly the split the plan needs:
``node.paint`` covers the ``QPainter`` calls inside it, ``scene.serialize``
covers the dict building, and ``view.paintEvent`` covers a whole frame.

Two modes, because the observer has a cost:

``frame``
    Only ``QGraphicsView.paintEvent`` is wrapped. One wrapper call per
    frame, so the headline frame numbers are clean.

``full``
    Every hot method is wrapped. At ~11k callbacks per zoomed-out frame the
    wrappers add a couple of milliseconds, so use this for the per-call
    breakdown, never for frame totals.
"""

import functools
import time

from typing import Dict, List, Optional, Tuple


class Samples:
    """A growable list of nanosecond samples with the usual percentiles."""

    __slots__ = ("values",)

    def __init__(self) -> None:
        self.values: List[int] = []

    def add(self, nanoseconds: int) -> None:
        self.values.append(nanoseconds)

    def clear(self) -> None:
        self.values.clear()

    def stats(self) -> Dict[str, float]:
        count = len(self.values)
        if count == 0:
            return {
                "count": 0,
                "total_us": 0.0,
                "mean_us": 0.0,
                "p50_us": 0.0,
                "p95_us": 0.0,
                "max_us": 0.0,
            }
        ordered = sorted(self.values)

        def percentile(fraction: float) -> float:
            index = int(round(fraction * (count - 1)))
            return ordered[index] / 1000.0

        return {
            "count": count,
            "total_us": round(sum(ordered) / 1000.0, 3),
            "mean_us": round(sum(ordered) / count / 1000.0, 3),
            "p50_us": round(percentile(0.50), 3),
            "p95_us": round(percentile(0.95), 3),
            "max_us": round(ordered[-1] / 1000.0, 3),
        }


#: ``(module, class, method, label)`` for full mode.
TARGETS: Tuple[Tuple[str, str, str, str], ...] = (
    ("nodeeditor.node_graphics_scene", "QDMGraphicsScene", "drawBackground", "scene.drawBackground"),
    ("nodeeditor.node_graphics_node", "QDMGraphicsNode", "paint", "node.paint"),
    ("nodeeditor.node_graphics_node", "QDMGraphicsNode", "boundingRect", "node.boundingRect"),
    ("nodeeditor.node_graphics_socket", "QDMGraphicsSocket", "paint", "socket.paint"),
    ("nodeeditor.node_graphics_socket", "QDMGraphicsSocket", "shape", "socket.shape"),
    ("nodeeditor.node_graphics_socket", "QDMGraphicsSocket", "boundingRect", "socket.boundingRect"),
    ("nodeeditor.node_graphics_edge", "QDMGraphicsEdge", "paint", "edge.paint"),
    ("nodeeditor.node_graphics_edge", "QDMGraphicsEdge", "shape", "edge.shape"),
    ("nodeeditor.node_graphics_edge", "QDMGraphicsEdge", "boundingRect", "edge.boundingRect"),
    ("nodeeditor.node_graphics_edge", "QDMGraphicsEdge", "calcPath", "edge.calcPath"),
    ("nodeeditor.node_scene", "Scene", "serialize", "scene.serialize"),
    ("nodeeditor.node_scene", "Scene", "deserialize", "scene.deserialize"),
    ("nodeeditor.node_scene_history", "SceneHistory", "createHistoryStamp", "history.createHistoryStamp"),
)


class Profiler:
    """Wraps methods, collects nanosecond samples, restores on demand."""

    def __init__(self) -> None:
        self.samples: Dict[str, Samples] = {}
        self.frames: Samples = Samples()
        self._restore: List[Tuple[object, str, object]] = []

    # -- setup ---------------------------------------------------------
    def wrap(self, obj: object, attribute: str, label: str) -> None:
        original = getattr(obj, attribute)
        sample = self.samples.setdefault(label, Samples())

        @functools.wraps(original)
        def timed(*args, **kwargs):
            started = time.perf_counter_ns()
            try:
                return original(*args, **kwargs)
            finally:
                sample.add(time.perf_counter_ns() - started)

        setattr(obj, attribute, timed)
        self._restore.append((obj, attribute, original))

    def wrap_frames(self, view_class: type) -> None:
        original = view_class.paintEvent
        frames = self.frames

        @functools.wraps(original)
        def timed(self, event):
            started = time.perf_counter_ns()
            try:
                return original(self, event)
            finally:
                frames.add(time.perf_counter_ns() - started)

        view_class.paintEvent = timed
        self._restore.append((view_class, "paintEvent", original))

    def install(self, mode: str = "full") -> None:
        self.wrap_frames(_view_class())
        if mode != "full":
            return
        for module_name, class_name, method, label in TARGETS:
            module = __import__(module_name, fromlist=[class_name])
            self.wrap(getattr(module, class_name), method, label)

    def restore(self) -> None:
        for obj, attribute, original in reversed(self._restore):
            setattr(obj, attribute, original)
        self._restore.clear()

    def reset(self) -> None:
        """Clear the samples in place; the wrappers keep their references."""
        for sample in self.samples.values():
            sample.clear()
        self.frames.clear()

    # -- output --------------------------------------------------------
    def report(self) -> Dict[str, Dict[str, float]]:
        report = {label: sample.stats() for label, sample in self.samples.items()}
        report["view.paintEvent"] = self.frames.stats()
        return report


def _view_class():
    from nodeeditor.node_graphics_view import QDMGraphicsView

    return QDMGraphicsView
