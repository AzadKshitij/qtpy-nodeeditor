# Installation

## Requirements

- Python 3.10 or newer
- A Qt binding: PyQt6 or PySide6. Any binding QtPy supports (PyQt5, PySide2,
  PyQt6, PySide6) works.

## From PyPI

Pick the extra that matches your binding:

```bash
pip install nodeeditor-qtpy[pyqt6]
```

```bash
pip install nodeeditor-qtpy[pyside6]
```

The extras exist only to pull in a binding — the framework itself depends on
`qtpy` and `orjson` and nothing else.

!!! tip "Already have a binding?"

    Installing without an extra is fine when PyQt or PySide is already in your
    environment:

    ```bash
    pip install nodeeditor-qtpy
    ```

    When several bindings are installed, QtPy chooses one using the `QT_API`
    environment variable:

    ```bash
    QT_API=pyside6 python my_app.py
    ```

## From source

```bash
git clone https://github.com/AzadKshitij/qtpy-nodeeditor.git
cd qtpy-nodeeditor
pip install -e ".[pyqt6]"
```

## If no binding is installed

Importing the package without any Qt binding raises a clear error:

```text
ImportError: No Qt binding found. Install nodeeditor-qtpy with one, e.g.
'pip install nodeeditor-qtpy[pyqt6]' or 'pip install nodeeditor-qtpy[pyside6]',
or install PyQt5/PySide2/PyQt6/PySide6 directly.
```

## Checking the install

```python
import nodeeditor

print(nodeeditor.__version__)
print(nodeeditor._QT_API_NAME)
```

The second line prints the binding that was detected, for example `pyqt6`.
