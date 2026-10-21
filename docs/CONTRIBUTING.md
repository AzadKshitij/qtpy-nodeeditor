# Documentation tooling

The site is built with [MkDocs](https://www.mkdocs.org/) and the
[Material for MkDocs](https://squidfunk.github.io/mkdocs-material/) theme.
The API reference is generated from the source with
[mkdocstrings](https://mkdocstrings.github.io/).

## Requirements

```
pip install -r requirements_docs.txt
```

## Build locally

```
mkdocs serve
```

The site is then available at <http://127.0.0.1:8000/> and rebuilds on save.

## Build once

```
mkdocs build --strict
```

`--strict` turns warnings into errors, which is what the CI workflow uses, so
a broken link or a malformed docstring fails the build instead of shipping.

## Layout

```
docs/
  index.md          home page
  installation.md   install options
  quickstart.md     first graph
  events.md         the event system
  guides/           task-focused guides
  api/              mkdocstrings pages, one per module group
  images/           screenshots used by the guides
```

The `nav` section of `mkdocs.yml` decides the sidebar. Pages that exist but
are not listed there are still built, they just do not show up in the
navigation.

## The images in the guides

Every guide opens with a picture. The files live in `docs/images/`, and each
one is referenced from the page listed below. To use your own screenshot
instead, **replace the file with the same name** — no markdown needs editing.

| File | Shows | Used by |
| --- | --- | --- |
| `docs/images/quickstart.png` | two connected nodes | `index.md`, `quickstart.md` |
| `docs/images/socket-shapes.png` | circle, square, triangle and chevron sockets | `guides/socket-shapes.md` |
| `docs/images/node-labels.png` | floating labels above nodes | `guides/node-labels.md` |
| `docs/images/edge-labels.png` | edges carrying labels | `guides/edge-labels.md` |
| `docs/images/group-nodes.png` | a group around two nodes | `guides/group-nodes.md`, `guides/node-grouping.md` |
| `docs/images/group-collapsed.png` | the same group collapsed | `guides/group-nodes.md`, `guides/node-grouping.md` |
| `docs/images/multi-input.png` | three nodes feeding one multi-input node | `guides/multi-input-nodes.md` |
| `docs/images/graph-algorithms.png` | a graph with the shortest path highlighted | `guides/graph-algorithms.md` |
| `docs/screenshot-calculator.png` | the calculator example | `index.md` |
| `docs/screenshot-example.png` | the editor window | `quickstart.md` |

To add a picture to a page, drop the file into `docs/images/` and reference it
relative to the page:

```markdown
![What the picture shows](../images/my-picture.png)
```

Pages in `docs/` use `images/my-picture.png`, pages in `docs/guides/` use
`../images/my-picture.png`.

## Regenerating the images

The screenshots in `docs/images/` are produced by a script, so they can be
refreshed when the look of the editor changes:

```
python scripts/make_doc_images.py
```

The script paints the scene into a `QImage` instead of taking a screenshot of
a window, so it needs a working Qt platform plugin but no visible screen. Do
not run it with `QT_QPA_PLATFORM=offscreen`: that platform has no fonts, and
the text comes out as empty boxes.
