# Performance results

All numbers are microseconds, measured on this machine with
`QT_QPA_PLATFORM=offscreen`, PyQt6 6.11.2, **1000 nodes / 999 edges** unless
noted. `--mode frame` numbers are per painted frame; `--mode full` numbers are
from the per-method wrappers and include the observer's cost.

Discipline: the baseline is re-run before a phase and must stay within ±5 %;
a phase that cannot beat ±3 % gets reverted.

Raw data: `phase-00-baseline-1000-frame.json`,
`phase-00-baseline-1000-full.json`, `phase-02-edge-cache-frame.json`,
`phase-02-edge-cache-full.json`.

## Phase 00 — baseline (main, before any change)

Frame totals, 1000 nodes:

| Scenario | paints | p50 frame | p95 frame |
|---|---|---|---|
| static, zoom 1.0 | 18 | 25,398 | 28,327 |
| static, zoom 0.35 | 13 | 40,759 | 43,456 |
| pan, zoom 1.0 | 30 | 2,596 | 3,782 |
| drag, zoom 0.35 | 30 | 13,363 | 39,093 |
| zoom steps | 12 | 42,087 | 55,690 |

Item work per frame, and the cost per call (full run):

| Metric | zoom 1.0 | zoom 0.35 |
|---|---|---|
| `node.paint` | 12 calls, 462 µs each | 60 calls, 316 µs each |
| `edge.boundingRect` | 1,007 calls, 9.8 µs | 1,059 calls, 10.1 µs |
| `edge.shape` | 1,007 calls, 4.0 µs | 1,059 calls, 4.2 µs |
| `edge.calcPath` | 1,015 calls, 3.4 µs | 1,119 calls, 3.5 µs |
| `edge.paint` | 8 calls, 34.3 µs | 60 calls, 20.8 µs |
| `socket.boundingRect` | 95 calls, 11.9 µs | hidden by LOD |
| `socket.paint` | 31 calls, 32.3 µs | hidden by LOD |
| `node.boundingRect` | 28 calls, 5.6 µs | 130 calls, 8.0 µs |
| `drawBackground` | 1,565 per frame | 5,310 per frame |

Operations:

| Operation | µs |
|---|---|
| `serialize()`, 1000 nodes | 143,274 |
| `createHistoryStamp()` | 149,060 |
| `deserialize()`, 1000 nodes | 218,690 (p50 209,386) |
| undo round trip (stamp + restore) | ~350,884 |
| one cut stroke across 999 edges | 191,448 (149,060 of it the history stamp) |
| one `topological_order()` | 1,801 |
| build 1000 nodes | 1,929,394 |

Primitive costs (`bench/micro.py`), which is the compiler question in one
table:

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

1. `serialize` is 143,274 µs and quadratic: Phase 1.
2. Edge paths are rebuilt 1,015–1,119 times per frame for 60–1,059 painted
   edges, and `boundingRect` / `shape` / `paint` all rebuild the same path:
   Phase 2.
3. `node.paint` is 316–462 µs per call and the largest single item at both
   zooms: Phase 3.
4. The frame as a whole is paint-bound: Phase 4 (raster cache).
5. `drawBackground` is 1.6–5.3 ms per frame: Phase 5a.

## Phase 01 — set-based serialize dedup

`Scene.serialize()` replaced four `any(...)` scans with one `seen` set per
collection. Output unchanged: first occurrence wins, order preserved.

| Operation | before | after | delta |
|---|---|---|---|
| `serialize()`, 1000 nodes | 146,360 | 25,029 | −83 % |
| `createHistoryStamp()`, 1000 nodes | 149,060 | 23,449 | −84 % |
| `serialize()`, 300 nodes | 16,225 | 8,223 | −49 % |

The curve is linear now: 3.3× the nodes costs 3× the time. Frame metrics do
not move: serialization is not in the paint path. Test gate: 121 passed, plus
an explicit check that a duplicated node or edge id is still dropped.

## Phase 02 — cache the edge path until the endpoints move

`QDMGraphicsEdge` now keeps `_path_cache`; `calcPath()` computes once and
`setPositions()` drops it. `shape()`, `boundingRect()`, `paint()` and
`intersectsWith()` all read the same path.

| Frame | before | after | delta |
|---|---|---|---|
| static, zoom 1.0 | 25,398 | 18,512 | −27 % |
| static, zoom 0.35 | 40,759 | 36,316 | −11 % |
| pan, zoom 1.0 | 2,596 | 2,033 | −22 % |
| drag, zoom 0.35 | 13,363 | 9,515 | −29 % |
| zoom steps | 42,087 | 39,064 | −7 % |

| Per call | before | after |
|---|---|---|
| `edge.calcPath` | 3.4 µs | 0.3 µs |
| `edge.shape` | 4.0 µs | 1.0 µs |
| `edge.boundingRect` | 9.8 µs | 6.5 µs |

Call counts are unchanged (~1,015/frame); each call is now a cache hit. Pixel
gate: both golden renders are byte-identical to the baseline. Tests: 121
passed.
