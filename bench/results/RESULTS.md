# Performance results

All numbers are microseconds, measured on this machine with
`QT_QPA_PLATFORM=offscreen`, PyQt6 6.11.2, **1000 nodes / 999 edges** unless
noted. `--mode frame` numbers are per painted frame; `--mode full` numbers are
from the per-method wrappers and include the observer's cost.

Raw data: `phase-00-baseline-1000-frame.json`,
`phase-00-baseline-1000-full.json`.

## Phase 00 — baseline (main, before any change)

Frame totals, 1000 nodes:

| Scenario | paints | p50 frame | p95 frame |
|---|---|---|---|
| static, zoom 1.0 | 18 | 26,779 | 28,704 |
| static, zoom 0.35 | 13 | 44,708 | 48,945 |
| pan, zoom 1.0 | 30 | 2,803 | 3,405 |
| drag, zoom 0.35 | 30 | 13,994 | 45,468 |
| zoom steps | 12 | 51,028 | 59,440 |

Item work per frame, and the cost per call (full run):

| Metric | zoom 1.0 | zoom 0.35 |
|---|---|---|
| `node.paint` | 12 calls, 743 µs each | 60 calls, 494 µs each |
| `edge.boundingRect` | 1,007 calls, 16.6 µs | 1,059 calls, 16.5 µs |
| `edge.shape` | 1,007 calls, 7.2 µs | 1,059 calls, 7.2 µs |
| `edge.calcPath` | 1,015 calls, 6.0 µs | 1,119 calls, 6.0 µs |
| `edge.paint` | 8 calls, 79.1 µs | 60 calls, 37.7 µs |
| `socket.boundingRect` | 95 calls, 17.8 µs | hidden by LOD |
| `socket.paint` | 31 calls, 49.4 µs | hidden by LOD |
| `node.boundingRect` | 28 calls, 9.0 µs | 130 calls, 10.9 µs |
| `drawBackground` | 3,282 µs per frame | 8,435 µs per frame |

Operations:

| Operation | µs |
|---|---|
| `serialize()`, 1000 nodes | 226,782 |
| `createHistoryStamp()` | 227,127 |
| `deserialize()`, 1000 nodes | 417,379 (p50 381,232) |
| undo round trip (stamp + restore) | ~608,000 |
| one cut stroke across 999 edges | 257,960 (181,718 of it the history stamp) |
| one `topological_order()` | 3,888 |
| build 1000 nodes | 2,298,794 |

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

1. `serialize` is 226,782 µs and quadratic: Phase 1.
2. Edge paths are rebuilt 1,015–1,119 times per frame for 60–1,059 painted
   edges, and `boundingRect` / `shape` / `paint` all rebuild the same path:
   Phase 2.
3. `node.paint` is 494–743 µs per call and the largest single item at both
   zooms: Phase 3.
4. The frame as a whole is paint-bound: Phase 4 (raster cache).
5. `drawBackground` is 3.3–8.4 ms per frame: Phase 5a.

## Phase 01 — set-based serialize dedup

`Scene.serialize()` replaced four `any(...)` scans with one `seen` set per
collection. Output unchanged: first occurrence wins, order preserved.

| Operation | before | after | delta |
|---|---|---|---|
| `serialize()`, 1000 nodes | 226,782 | 24,620 | −89 % |
| `createHistoryStamp()`, 1000 nodes | 227,127 | 27,111 | −88 % |
| `serialize()`, 300 nodes | 16,225 | 8,223 | −49 % |

The 1000-node curve is linear now: 3.3× the nodes costs 3× the time, where the
old scan would have cost 11×. Frame metrics do not move: serialization is not
in the paint path. Test gate: 121 passed, plus an explicit check that a
duplicated node or edge id is still dropped.
