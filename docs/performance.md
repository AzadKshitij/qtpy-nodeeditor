# Performance

This release focuses on two things that actually cost time in a large graph:
redundant Qt object creation and redundant Python bookkeeping. The editor is a
thin Python layer over Qt's C++ scene graph, so compiling the Python with
Cython, mypyc or Mojo does not reach the hot path. A Python call costs about
0.05 µs here, one Qt call about 1.5 µs, and `QPainterPath.simplified()` about
23 µs.

## Measuring it yourself

The repository ships a deterministic harness under `bench/`. Build a 1000-node
scene and take the cleanest of three full runs:

```bash
.venv\Scripts\python.exe -m bench.run_bench --nodes 1000 --mode frame --runs 3
.venv\Scripts\python.exe -m bench.run_bench --nodes 1000 --mode full --runs 1
```

`frame` mode wraps only `QGraphicsView.paintEvent`, so the frame numbers do not
include the observer's cost. `full` mode wraps every hot method and gives the
per-call numbers. Both run with `QT_QPA_PLATFORM=offscreen` and write the
aggregated data as JSON. The summarized results for each phase are in
`bench/results/RESULTS.md`.

## Results

1000 nodes / 999 edges, PyQt6 6.11.2, 1000×700 viewport. Numbers are
microseconds, best of three runs on a machine with ~30% background CPU.

| Frame | before | now | Delta |
|---|---|---|---|
| static, zoom 1.0 | 22,476 | 11,520 | −49% |
| static, zoom 0.35 | 38,173 | 22,726 | −40% |
| pan | 2,185 | 1,366 | −37% |
| drag, zoom 0.35 | 11,893 | 2,091 | −82% |
| zoom steps | 42,389 | 25,253 | −40% |

| Operation | before | now |
|---|---|---|
| `serialize()` at 1000 nodes | 143,274 µs | 25,029 µs |
| one cut stroke | 191,448 µs | 62,241 µs |
| `edge.calcPath` per call | 3.4 µs | 0.3 µs |
| `edge.boundingRect` per call | 9.8 µs | 0.4 µs |
| `node.paint` per call at zoom 1.0 | 462 µs | 272 µs |

The practical headline is node dragging: at 1000 nodes a step fell from about
12 ms to about 2 ms.

## What changed

- `Scene.serialize()` uses a `set` per collection instead of four O(n²)
  `any(...)` dedup scans.
- `QDMGraphicsEdge` caches its `QPainterPath` and bounding rectangle until the
  endpoints move. `paint()`, `shape()`, `boundingRect()` and
  `intersectsWith()` reuse them.
- `QDMGraphicsNode` builds its three body paths once instead of allocating
  them and calling `simplified()` four times on every paint.
- `Edge.updatePositions()` sets both endpoints in one call, so an edge adopts
  its geometry once per move.

## What did not pay off

These were measured and deliberately left out:

- **Grid line cache** — A/B showed no gain; the 5.3 ms at zoom 0.35 is C++
  `drawLines`, not Python list construction.
- **Device raster cache on nodes** — 23–45% faster frames but visibly softer
  node outlines (2.07% of pixels change, max delta 88).
- **Full viewport repaint during gestures** — 11,401 µs per pan step versus
  1,366 µs, and unnecessary once item rectangles declare what they paint.

## Repaint correctness

Several items used to paint outside the rectangle they declared, or changed
geometry without declaring it first. Qt repaints by the old declared rectangle,
so the stale pixels survived as smears:

- the cut stroke now declares its geometry change before its points are
  replaced
- node rectangles include the outline stroke they paint
- an edge adopts both ends in one geometry change per move

The fixes came from the same canvas work in TriggerEditor and are verified by
framebuffer captures of a real window plus `tests/test_140_cut_line.py`.
