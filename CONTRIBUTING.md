# Contributing to PyQt-Node-Editor

Bug fixes, feature additions, tests, documentation and more can be contributed 
via [issues](https://gitlab.com/pavel.krupala/pyqt-node-editor/issues) and/or [merge_requests](https://gitlab.com/pavel.krupala/pyqt-node-editor/merge_requests). All contributions are welcome.

## Contributors

- Richard Boltze
- RoniPerson 

## Bug fixes, feature additions, etc.

Please send a merge request to the master branch. Please include [documentation](https://pyqt-node-editor.readthedocs.io/en/latest/). Tests or documentation without bug fixes or feature additions are welcome too. Feel free to ask questions [via issues](https://gitlab.com/pavel.krupala/pyqt-node-editor/issues/new), 

- Create a branch from master.
- Develop bug fixes, features, tests, etc.
- Test your code on Python 3.x. 
- Create a merge request to merge the changes from your branch to the PyQt-Node-Editor master.

### Guidelines

- Separate code commits from reformatting commits.
- Provide tests for any newly added code when possible.

## Building distributions

`uv_build` is the declared build backend. To build the wheel and sdist:

```
uv build
```

Hatchling configuration is kept in `pyproject.toml` as a fallback. To use it,
replace the `[build-system]` table with:

```
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

Both backends ship the same wheel and sdist contents.

## Releasing

Releases are published from GitHub Actions so that PyPI records provenance
(PEP 740 attestations) for every upload. A local upload shows up on PyPI as
"Without provenance", so avoid publishing from a workstation for releases.

1. Update `version` in `pyproject.toml`.
2. Tag the commit and create a GitHub release. The `Publish` workflow
   (`.github/workflows/publish.yml`) builds the distributions and uploads them
   to PyPI.
3. For a rehearsal, run the same workflow manually
   (*Actions -> Publish -> Run workflow*) and pick `testpypi`.

Trusted publishing must be set up once per index: on PyPI, add a *Pending
Publisher* with the project name `nodeeditor-qtpy`, owner `AzadKshitij`,
repository `qtpy-nodeeditor`, workflow `publish.yml` and environment `pypi`
(or `testpypi` for the test index). Create the matching GitHub environment.

To publish by hand instead, build and upload with a token:

```
uv build
uv publish --token <pypi-token>
```

## Documentation

The documentation site is built with MkDocs and the Material for MkDocs theme,
and is published to GitHub Pages by the `Docs` workflow:
<https://azadkshitij.github.io/qtpy-nodeeditor/>

The API reference is generated from the docstrings in the source with
mkdocstrings, so it always matches the code. To work on the site:

```
pip install -r requirements_docs.txt
pip install -e ".[pyqt6]"
mkdocs serve
```

`mkdocs build --strict` builds it once and fails on any warning, which is
what CI runs. See [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) for the layout.

### Publishing the site

The site is rebuilt and deployed when a commit pushed to `main` carries
**"publish"** in its message:

```
git commit -m "docs: update the guides, publish"
git push
```

The keyword is matched case-insensitively, so `publish`, `Publish` and
`published` all work. Any other push leaves the live site untouched, which
keeps it stable while you work. The workflow can also be started by hand from
the *Actions* tab.

The first deployment needs one setting in the repository: *Settings → Pages →
Build and deployment → Source* set to **GitHub Actions**.

## Reporting Issues

When reporting issues, please include code that reproduces the issue and whenever possible, an image that demonstrates the issue. Please upload images to GitLab, not to third-party file hosting sites. If necessary, add the image to a zip or tar archive.

The best reproductions are self-contained scripts with minimal dependencies. If you are using a framework, try to replicate the issue just using PyQt-Node-Editor.

### Provide details

- What did you do?
- What did you expect to happen?
- What actually happened?
- What versions of PyQt-Node-Editor and Python are you using?
