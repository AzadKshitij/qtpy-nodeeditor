# Performance results

All numbers are microseconds, measured on this machine with
`QT_QPA_PLATFORM=offscreen`, PyQt6, 300 nodes / 299 edges unless noted.
`--mode frame` numbers are per painted frame; `--mode full` numbers are from
the per-method wrappers and include the observer's cost.

Raw data: `phase-00-baseline-frame.json`, `phase-00-baseline-full.json`.

## Phase 00 — baseline (main, before any change)

Frame totals, 300 nodes:

| Scenario | paints | p50 frame | p95 frame |
|---|---|---|---|
| static, zoom 1.0 | 18 | 17,867 | 20,173 |
| static, zoom 0.35 | 13 | 33,992 | 36,236 |
| pan, zoom 1.0 | 30 | 6,017 | 6,867 |
| drag, zoom 0.35 | 30 | 5,033 | 31,796 |
| zoom steps | 12 | 36,627 | 54,754 |

Per-frame item work, from the full run (total / painted frames):

| Metric | zoom 1.0 | zoom 0.35 |
|---|---|---|
| `node.paint` | 6,245 (12 calls) | 17,435 (60 calls) |
| `scene.drawBackground` | 2,027 | 4,749 |
| `edge.boundingRect` | 3,602 (307 calls) | 3,707 (359 calls) |
| `edge.shape` | 1,483 (307) | 1,534 (359) |
| `edge.calcPath` | 1,261 (315) | 1,482 (419) |
| `edge.paint` | 394 (8) | 1,417 (60) |
| `socket.boundingRect` | 1,669 (95) | — (LOD hidden) |
| `socket.paint` | 1,200 (31) | — |
| `node.boundingRect` | 210 (28) | 989 (130) |

Per-call cost (full run):

| Call | p50 µs |
|---|---|
| `node.paint` | 530 (zoom 1.0), 254 (zoom 0.35) |
| `edge.boundingRect` | 10.9 |
| `socket.boundingRect` | 13.9 |
| `socket.paint` | 36.2 |
| `edge.shape` | 4.4 |
| `edge.calcPath` | 3.7 |
| `edge.paint` | 47.5 |

Operations:

| Operation | µs |
|---|---|
| `serialize()`, 300 nodes | 16,225 |
| `createHistoryStamp()` | 16,760 |
| `deserialize()`, 300 nodes | 61,056 |
| undo round trip (stamp + restore) | ~84,000 |
| one cut stroke across 300 edges | 27,609 |
| 20 × `topological_order()`, 300 nodes | 9,626 |
| build 300 nodes | 523,122 |

Primitive costs (`bench/micro.py`), which is the compiler question in one table:

| Operation | µs |
|---|---|
| Python function call | 0.054 |
| `QPointF(1, 2)` | 0.707 |
| `QPainterPath()` | 0.434 |
| `path.addRoundedRect(...)` | 2.504 |
| `path.cubicTo(...)` | 4.831 |
| `QLine(...)` | 1.006 |
| `QColor(...)` | 2.088 |
| `path.simplified()` | 22.768 |

### What the baseline says to do first

1. `serialize` is 16.2 ms at 300 nodes and grows quadratically: Phase 1.
2. Edge paths are rebuilt 315–419 times per frame for 60–359 painted edges:
   Phase 2.
3. `node.paint` is the largest single item at both zooms: Phase 3.
4. The frame as a whole is paint-bound: Phase 4 (raster cache).
5. `drawBackground` is 2.0–4.7 ms per frame: Phase 5a.

## Phase 01 — set-based serialize dedup

`Scene.serialize()` replaced four `any(...)` scans with one `seen` set per
collection. Output unchanged: first occurrence wins, order preserved.

| Operation | before | after | delta |
|---|---|---|---|
| `serialize()`, 300 nodes | 16,225 | 8,223 | −49 % |
| `createHistoryStamp()`, 300 nodes | 16,760 | 8,458 | −50 % |
| `serialize()`, 1000 nodes | ~180,000 (quadratic) | 24,620 | linear now |

Frame metrics do not move: serialization is not in the paint path. Test gate:
121 passed, plus an explicit check that a duplicated node or edge id is still
dropped.
