"""Render the two benchmark views to PNG, for pixel regression checks."""

import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from bench.scene_builder import app, build_scene  # noqa: E402
from bench.run_bench import HEIGHT, WIDTH, close_view, make_view  # noqa: E402

from qtpy.QtCore import QRectF  # noqa: E402
from qtpy.QtGui import QImage, QPainter  # noqa: E402

VIEWS = (
    ("zoom-1.00", 1.0, (390, 320)),
    ("zoom-0.35", 0.35, (1260, 800)),
)


def render(scene, zoom: float, focus, path: str) -> None:
    view = make_view(scene, zoom, focus)
    try:
        image = QImage(WIDTH, HEIGHT, QImage.Format.Format_ARGB32_Premultiplied)
        image.fill(0xFF1E1E1E)
        painter = QPainter(image)
        painter.setRenderHints(view.renderHints())
        source = view.mapToScene(view.viewport().rect()).boundingRect()
        try:
            scene.grScene.render(
                painter, QRectF(0, 0, WIDTH, HEIGHT), source)
        finally:
            painter.end()
        if not image.save(path):
            raise RuntimeError("could not write %s" % path)
    finally:
        close_view(view)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=os.path.join(ROOT, "bench", "golden"))
    parser.add_argument("--nodes", type=int, default=300)
    args = parser.parse_args(argv)

    app()
    scene, _ = build_scene(args.nodes)
    os.makedirs(args.out, exist_ok=True)
    for name, zoom, focus in VIEWS:
        path = os.path.join(args.out, name + ".png")
        render(scene, zoom, focus, path)
        print("wrote", path)
    scene.clear()
    return 0


if __name__ == "__main__":
    sys.exit(main())
