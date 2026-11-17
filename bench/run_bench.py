"""The measurement harness for the performance phases.

Usage (from the repository root):

    python -m bench.run_bench --phase 00-baseline --nodes 300 --mode frame
    python -m bench.run_bench --phase 00-baseline --nodes 300 --mode full

``frame`` wraps only ``QGraphicsView.paintEvent``: one timer per frame, so the
headline microseconds are not distorted by the observer. ``full`` wraps every
hot method and is what the per-call tables come from.
"""

import argparse
import json
import os
import platform
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from bench.scene_builder import app, build_scene  # noqa: E402
from bench.instrument import Profiler  # noqa: E402
from bench.micro import run_micro  # noqa: E402

from qtpy.QtCore import QPointF  # noqa: E402
from qtpy.QtGui import QFontInfo  # noqa: E402
from qtpy.QtWidgets import QApplication  # noqa: E402

from nodeeditor.node_graphics_view import QDMGraphicsView  # noqa: E402

WIDTH = 1000
HEIGHT = 700
WARMUP = 3


def make_view(scene, zoom: float, focus) -> QDMGraphicsView:
    view = QDMGraphicsView(scene.grScene)
    view.resize(WIDTH, HEIGHT)
    view.show()
    app().processEvents()
    view.setSceneRect(scene.grScene.itemsBoundingRect().adjusted(-400, -400, 400, 400))
    view.resetTransform()
    if zoom != 1.0:
        view.scale(zoom, zoom)
    view.centerOn(focus[0], focus[1])
    app().processEvents()
    return view


def close_view(view: QDMGraphicsView) -> None:
    view.setScene(None)
    view.close()
    view.deleteLater()
    app().processEvents()


def render_frame(view: QDMGraphicsView) -> int:
    started = time.perf_counter_ns()
    view.viewport().repaint()
    return time.perf_counter_ns() - started


def scenario(profiler: Profiler, function) -> dict:
    profiler.reset()
    started = time.perf_counter_ns()
    try:
        function()
    finally:
        elapsed = (time.perf_counter_ns() - started) / 1000.0
    report = profiler.report()
    report["scenario_us"] = round(elapsed, 3)
    return report


# -- scenarios ---------------------------------------------------------

def static_render(view: QDMGraphicsView, rounds: int) -> None:
    for _ in range(rounds + WARMUP):
        render_frame(view)


def pan_steps(view: QDMGraphicsView, steps: int) -> None:
    bar = view.horizontalScrollBar()
    for _ in range(steps):
        bar.setValue(bar.value() + 3)
        app().processEvents()


def drag_steps(node, steps: int) -> None:
    for _ in range(steps):
        position = node.pos
        node.setPos(position.x() + 1, position.y())
        app().processEvents()


def zoom_steps(view: QDMGraphicsView, steps: int) -> None:
    for _ in range(steps):
        view.scale(0.9, 0.9)
        app().processEvents()


def undo_burst(scene, steps: int) -> None:
    for _ in range(steps):
        scene.history.storeHistory("bench")
        scene.history.undo()


def serialize_repeatedly(scene, repeats: int) -> None:
    for _ in range(repeats):
        scene.serialize()


def cut_once(scene, view: QDMGraphicsView) -> None:
    view.cutline.line_points = [QPointF(-100, 160), QPointF(2600, 160)]
    view.cutIntersectingEdges()


def graph_repeatedly(scene, repeats: int) -> None:
    for _ in range(repeats):
        scene.topological_order()


# -- report ------------------------------------------------------------

def print_table(report: dict) -> None:
    rows = sorted(
        ((label, stats) for label, stats in report.items() if isinstance(stats, dict)),
        key=lambda item: item[1].get("total_us", 0.0),
        reverse=True,
    )
    print("%-28s %8s %12s %10s %10s %10s" % (
        "label", "count", "total_us", "mean_us", "p50_us", "p95_us"))
    for label, stats in rows:
        print("%-28s %8d %12.1f %10.3f %10.3f %10.3f" % (
            label,
            stats.get("count", 0),
            stats.get("total_us", 0.0),
            stats.get("mean_us", 0.0),
            stats.get("p50_us", 0.0),
            stats.get("p95_us", 0.0),
        ))


def environment() -> dict:
    import qtpy
    from qtpy.QtCore import qVersion

    return {
        "python": platform.python_version(),
        "qtpy_api": qtpy.API_NAME,
        "qt": qVersion(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "font": QFontInfo(QApplication.font()).family(),
        "offscreen": os.environ.get("QT_QPA_PLATFORM", ""),
    }


def commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return ""


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", default="00-baseline")
    parser.add_argument("--nodes", type=int, default=1000)
    parser.add_argument("--mode", choices=("frame", "full"), default="frame")
    parser.add_argument("--json", default="")
    parser.add_argument("--skip-micro", action="store_true")
    parser.add_argument("--skip-cut", action="store_true")
    args = parser.parse_args(argv)

    app()

    built = time.perf_counter_ns()
    scene, nodes = build_scene(args.nodes)
    build_us = (time.perf_counter_ns() - built) / 1000.0

    profiler = Profiler()
    profiler.install(args.mode)
    results = {}

    try:
        view = make_view(scene, 1.0, (390, 320))
        try:
            results["static_zoom_1.0"] = scenario(
                profiler, lambda: static_render(view, 15))
            results["pan_zoom_1.0"] = scenario(
                profiler, lambda: pan_steps(view, 30))
        finally:
            close_view(view)

        view = make_view(scene, 0.35, (1260, 800))
        try:
            results["static_zoom_0.35"] = scenario(
                profiler, lambda: static_render(view, 10))
            results["drag_zoom_0.35"] = scenario(
                profiler, lambda: drag_steps(nodes[0], 30))
        finally:
            close_view(view)

        view = make_view(scene, 1.0, (390, 320))
        try:
            results["zoom_steps"] = scenario(
                profiler, lambda: zoom_steps(view, 12))
        finally:
            close_view(view)

        results["undo"] = scenario(
            profiler, lambda: undo_burst(scene, 10))
        results["serialize"] = scenario(
            profiler, lambda: serialize_repeatedly(scene, 5))
        results["graph"] = scenario(
            profiler, lambda: graph_repeatedly(scene, 20))

        if not args.skip_cut:
            cut_scene, _ = build_scene(args.nodes)
            cut_view = make_view(cut_scene, 1.0, (390, 320))
            try:
                results["cut"] = scenario(
                    profiler, lambda: cut_once(cut_scene, cut_view))
            finally:
                close_view(cut_view)
            cut_scene.clear()
    finally:
        profiler.restore()

    output = {
        "phase": args.phase,
        "commit": commit(),
        "mode": args.mode,
        "nodes": args.nodes,
        "build_us": round(build_us, 3),
        "env": environment(),
        "micro": {} if args.skip_micro else run_micro(),
        "scenarios": results,
    }

    for name, report in results.items():
        print("\n== %s ==  scenario %.1f us" % (name, report["scenario_us"]))
        print_table(report)

    if args.json:
        directory = os.path.dirname(os.path.abspath(args.json))
        os.makedirs(directory, exist_ok=True)
        with open(args.json, "w", encoding="utf-8") as handle:
            json.dump(output, handle, indent=2)
        print("\nwrote %s" % args.json)

    return 0


if __name__ == "__main__":
    sys.exit(main())
