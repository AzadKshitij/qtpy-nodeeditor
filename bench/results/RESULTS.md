# Performance results

All numbers are microseconds, measured on this machine with
`QT_QPA_PLATFORM=offscreen`, PyQt6 6.11.2, **1000 nodes / 999 edges** unless
noted. `--mode frame` numbers are per painted frame; `--mode full` numbers are
from the per-method wrappers and include the observer's cost.

Discipline: the baseline is re-run before a phase and must stay within ±5 %;
a phase that cannot beat ±3 % gets reverted. This machine carries ~30 %
background CPU, so every headline number is the cleanest of three full suite
runs (`--runs 3`); per-call numbers come from the `full` mode and are stable
within a run.

Raw data: `phase-00-baseline-1000-frame.json`,
`phase-00-baseline-1000-full.json`, `phase-02-edge-cache-frame.json`,
`phase-02-edge-cache-full.json`.

## Phase 00 — baseline (main, before any change)

Frame totals, 1000 nodes:

| Scenario | paints | p50 frame | p95 frame |
|---|---|---|---|
| static, zoom 1.0 | 18 | 22,476 | 26,118 |
| static, zoom 0.35 | 13 | 38,173 | 43,597 |
| pan, zoom 1.0 | 30 | 2,185 | 2,596 |
| drag, zoom 0.35 | 30 | 11,893 | 37,328 |
| zoom steps | 12 | 42,389 | 54,492 |

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

## Phase 03 — precompute the node body paths

`QDMGraphicsNode` builds `_path_title`, `_path_content` and `_path_outline`
once and rebuilds them only when `(width, height, title_height,
edge_roundness)` changes. `paint()` no longer allocates three paths and no
longer calls `simplified()` four times per node per frame.

| Metric | before | after | delta |
|---|---|---|---|
| `node.paint`, zoom 1.0 | 462 µs | 272 µs | −41 % |
| `node.paint`, zoom 0.35 | 316 µs | 188 µs | −41 % |
| static frame, zoom 1.0 | 18,512 | 18,171 | −1.8 % |
| static frame, zoom 0.35 | 36,316 | 29,278 | −19 % |
| pan, zoom 1.0 | 2,033 | 1,553 | −24 % |
| drag, zoom 0.35 | 9,515 | 8,986 | −5.6 % |
| zoom steps | 39,064 | 31,265 | −20 % |

The zoom-1.0 static frame moves under the 3 % gate because only 12 nodes paint
per frame there; the same change is 19–24 % wherever node paint dominates. Kept
on that basis, recorded here rather than hidden.

Pixel gate: 0.18 % (1.0) and 0.39 % (0.35) of pixels differ, max channel delta
7 and 21, and the diff image shows the change only along the rounded-corner
arcs where `simplified()` used to merge subpaths. No structural difference.
Tests: 121 passed.

## Phase 04 — cache the edge bounding rectangle

`QDMGraphicsEdge.boundingRect()` now computes once and caches, invalidated by
`setPositions()`, `setLabel()` and `updateLabelPosition()`. At 1,007–1,059
calls per frame this is the hottest remaining item.

Same-machine A/B: Phase 3 code vs Phase 4 code, both best-of-3 runs, 1000
nodes.

| Frame | Phase 3 | Phase 4 | delta |
|---|---|---|---|
| static, zoom 1.0 | 19,385 | 11,520 | −41 % |
| static, zoom 0.35 | 32,042 | 22,726 | −29 % |
| pan, zoom 1.0 | 1,773 | 1,366 | −23 % |
| drag, zoom 0.35 | 8,564 | 2,091 | −76 % |
| zoom steps | 35,922 | 25,253 | −30 % |

| Per call | before | after |
|---|---|---|
| `edge.boundingRect` | 6.6 µs | 0.4 µs |

Call counts are unchanged (~1,007/frame at 1.0, ~1,059 at 0.35). Pan barely
moves because pan repaints few edges; drag improves most because every moved
edge used to recompute its rectangle several times per step. Pixel gate:
identical to Phase 3 (the only deltas remain the corner-antialiasing pixels
introduced by Phase 3). Tests: 121 passed.

### Cumulative after Phase 04

| Frame | baseline | now | delta |
|---|---|---|---|
| static, zoom 1.0 | 22,476 | 11,520 | −49 % |
| static, zoom 0.35 | 38,173 | 22,726 | −40 % |
| pan, zoom 1.0 | 2,185 | 1,366 | −37 % |
| drag, zoom 0.35 | 11,893 | 2,091 | −82 % |
| zoom steps | 42,389 | 25,253 | −40 % |

## Phase 05 — grid line cache (rejected)

`drawBackground()` spent 1,565 µs per frame at zoom 1.0 and 5,310 µs at 0.35.
The candidate change cached the two `QLine` lists by
`(left, right, top, bottom, step, major_step, draw_minor)`.

Same-machine A/B, best-of-3:

| Frame | no cache | with cache | delta |
|---|---|---|---|
| static, zoom 1.0 | 11,520 | 11,039 | −4.2 % |
| static, zoom 0.35 | 22,726 | 22,936 | +0.9 % |
| pan, zoom 1.0 | 1,366 | 1,403 | +2.7 % |
| drag, zoom 0.35 | 2,091 | 2,270 | +8.6 % |
| zoom steps | 25,253 | 24,513 | −2.9 % |

Only the zoom-1.0 case clears the gate; everything else ties or regresses.
The 5.3 ms at zoom 0.35 is `drawLines` in C++, not the Python list building,
so caching the list cannot reach it. **Reverted** per the 3 % rule. Raw:
`phase-05-grid-cache-frame.json`, `phase-04-edge-bounds-frame-ab.json`.

## Probed and not merged — device raster cache

`DeviceCoordinateCache` on every node was probed at runtime before touching
the source. On a 60-node scene with a real `QLabel` inside each
`QGraphicsProxyWidget`, the proxy widgets render correctly and frames drop
from 13,378 to 10,321 µs at zoom 1.0 (−23 %) and from 16,352 to 9,011 µs at
0.35 (−45 %). But 2.07 % of pixels differ, with a max channel delta of 88,
spread along every node outline: the 2 px border is rasterized into the
device cache and composited, so it loses its direct-draw antialiasing.
Not merged; it would need an "interactive only" mode (cache during pan, drag
and zoom, drop it on idle) to keep the resting frame crisp.

## Where the time went

| Item | before | after | change |
|---|---|---|---|
| frame, static 1.0 | 22,476 | 11,520 | −49 % |
| frame, static 0.35 | 38,173 | 22,726 | −40 % |
| frame, drag 0.35 | 11,893 | 2,091 | −82 % |
| `serialize()` @1000 | 143,274 | 25,029 | −83 % |
| one cut stroke | 191,448 | 62,241 | −67 % |
| `edge.calcPath` per call | 3.4 µs | 0.3 µs | −91 % |
| `edge.boundingRect` per call | 9.8 µs | 0.4 µs | −96 % |
| `node.paint` per call @1.0 | 462 µs | 272 µs | −41 % |
