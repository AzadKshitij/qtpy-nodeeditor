# -*- encoding: utf-8 -*-
"""
Module with some helper functions
"""
from typing import cast
from nodeeditor import _QT_API_NAME as QT_API
from qtpy.QtCore import QFile, QByteArray
from qtpy.QtWidgets import QApplication

from nodeeditor.utils_no_qt import pp, dumpException


def loadStylesheet(filename: str) -> None:
    """
    Loads an qss stylesheet to the current QApplication instance

    :param filename: Filename of qss stylesheet
    :type filename: str
    Raises:
        RuntimeError: If no QApplication instance exists
    """
    print('STYLE loading:', filename)
    # app = QApplication.instance()
    app = cast(QApplication, QApplication.instance())
    if app is None:
        raise RuntimeError("No QApplication instance found")

    file = QFile(filename)
    file.open(QFile.OpenModeFlag.ReadOnly | QFile.OpenModeFlag.Text)
    try:
        stylesheet: QByteArray = file.readAll()
        stylesheet_str = stylesheet.data().decode('utf-8')
        app.setStyleSheet(stylesheet_str)
    finally:
        file.close()


def loadStylesheets(*args) -> None:
    """
    Loads multiple qss stylesheets. Concatenates them together and applies the final stylesheet to the current QApplication instance

    :param args: variable number of filenames of qss stylesheets
    :type args: str, str,...
    Raises:
        RuntimeError: If no QApplication instance exists
    """
    app = cast(QApplication, QApplication.instance())
    if app is None:
        raise RuntimeError("No QApplication instance found")

    res = ''
    for arg in args:
        file = QFile(arg)
        file.open(QFile.OpenModeFlag.ReadOnly | QFile.OpenModeFlag.Text)
        try:
            stylesheet: QByteArray = file.readAll()
            res += "\n" + stylesheet.data().decode('utf-8')
        finally:
            file.close()
    app.setStyleSheet(res)


def isCTRLPressed(event):
    """
    Checks whether the Control key is held down in the given event.

    :param event: Qt's mouse or key event
    :type event: ``QEvent``
    :return: the Control modifier of the event, truthy when the key is held
    :rtype: ``int``
    """
    from qtpy.QtCore import Qt
    if QT_API in ("pyqt5", "pyside2"):
        return event.modifiers() & Qt.CTRL
    if QT_API in ("pyqt6", "pyside6"):
        return event.modifiers() & Qt.KeyboardModifier.ControlModifier


def isSHIFTPressed(event):
    """
    Checks whether the Shift key is held down in the given event.

    :param event: Qt's mouse or key event
    :type event: ``QEvent``
    :return: the Shift modifier of the event, truthy when the key is held
    :rtype: ``int``
    """
    from qtpy.QtCore import Qt
    if QT_API in ("pyqt5", "pyside2"):
        return event.modifiers() & Qt.SHIFT
    if QT_API in ("pyqt6", "pyside6"):
        return event.modifiers() & Qt.KeyboardModifier.ShiftModifier


def isALTPressed(event):
    """
    Checks whether the Alt key is held down in the given event.

    :param event: Qt's mouse or key event
    :type event: ``QEvent``
    :return: the Alt modifier of the event, truthy when the key is held
    :rtype: ``int``
    """
    from qtpy.QtCore import Qt
    if QT_API in ("pyqt5", "pyside2"):
        return event.modifiers() & Qt.ALT
    if QT_API in ("pyqt6", "pyside6"):
        return event.modifiers() & Qt.KeyboardModifier.AltModifier
