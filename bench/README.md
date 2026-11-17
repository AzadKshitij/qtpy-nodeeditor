# Performance harness

Reproducible microsecond measurements for the editor's hot paths. Nothing
here ships in the wheel (`pyproject.toml` names `nodeeditor` as the module).

## Run

```bash
python -m bench.run_bench --phase 00-baseline --nodes 1000 --mode frame \
    --json bench/results/phase-00-baseline-frame.json
python -m bench.run_bench --phase 00-baseline --nodes 1000 --mode full \
    --json bench/results/phase-00-baseline-full.json
```

* `--mode frame` wraps only `QGraphicsView.paintEvent`, so the headline
  frame numbers are not distorted by the observer.
* `--mode full` wraps every hot method. Use it for per-call microseconds;
  at ~11k callbacks per zoomed-out frame the wrappers add a couple of
  milliseconds.

## What it measures

| Scenario | What it drives |
|---|---|
| `static_zoom_1.0` | full paint of ~8 visible nodes at 1:1 |
| `static_zoom_0.35` | full paint of ~60 visible nodes and ~480 edges |
| `pan_zoom_1.0` | 30 scroll steps through `BoundingRectViewportUpdate` |
| `drag_zoom_0.35` | 30 one-pixel node moves, edges refresh |
| `zoom_steps` | 12 zoom-out steps |
| `undo` | 10 `storeHistory` + `undo` round trips |
| `serialize` | 5 full-scene `serialize()` calls |
| `cut` | one cut stroke across 300 edges |
| `graph` | 20 `topological_order()` calls |

Every run also records the primitive costs (`bench/micro.py`): one Python
call versus one `QPointF`, one `QPainterPath`, one `path.simplified()`, and
so on. That is the table that says whether a Python compiler could matter.

## Discipline

1. Run the baseline before a phase and confirm it is within ±5 % of the
   previous run on the same machine; otherwise discard the comparison.
2. Change one thing, re-run both modes, record incremental and cumulative.
3. Keep a change only if it beats measurement noise (~3 %); otherwise revert
   it rather than carry the complexity.
