"""
A reusable canvas Comment (sticky note) for :class:`~nodeeditor.node_scene.Scene`.

A `Comment` is a pure visual item, like :class:`~nodeeditor.node_group.Group`.
It has no sockets, never runs, and takes no part in graph evaluation. It holds
multi-line plain text, can be moved and selected with the mouse, and edits its
text inline with a double click.

Editing semantics
-----------------
``begin_edit()`` puts an inline :class:`~qtpy.QtWidgets.QGraphicsTextItem`
editor over the note. The edit ends in one of three ways:

- **Focus out** (clicking elsewhere) commits the text. A change is stored as a
  scene-history entry named ``"Edited comment"``.
- **Escape** cancels the edit and restores the text the note had when editing
  began. Nothing is written to the history.
- ``finish_edit(commit=True)`` commits explicitly and ``cancel_edit()``
  discards explicitly, for applications that drive editing from their own UI.

Programmatic ``setText(..., store_history=True)`` also stores a history entry.
``setText`` defaults to no history entry so loading and generated notes do not
pollute the undo stack. The history snapshot includes comments through
:meth:`Scene.serialize`, so undo and redo restore comment text, position, size,
colours and z-order.

Serialized JSON shape
---------------------
Comments live in the scene's additive ``"comments"`` list. Files written before
comments existed have no such key and load unchanged::

    {
      "id": 1234,
      "type": "Comment",
      "version": 1,
      "text": "first line\\nsecond line",
      "x": 40.0,
      "y": 25.0,
      "w": 240.0,
      "h": 110.0,
      "z": 1.0,
      "style": {
        "background": [255, 248, 214, 232],
        "border": [190, 175, 120, 255],
        "text": [35, 35, 35, 255]
      }
    }

``x``/``y`` are scene coordinates. ``w``/``h`` are the current outer size after
auto-sizing. ``z`` is the item's z-value, so front/back order survives a save.
"""

from typing import TYPE_CHECKING

from qtpy.QtCore import Qt
from qtpy.QtGui import QBrush, QColor, QPainter, QPen, QTextCursor
from qtpy.QtWidgets import (
    QGraphicsItem,
    QGraphicsRectItem,
    QGraphicsTextItem,
    QMenu,
)

from nodeeditor.node_serializable import Serializable
from nodeeditor.utils_no_qt import dumpException

if TYPE_CHECKING:
    from nodeeditor.node_scene import Scene


COMMENT_SERIALIZATION_VERSION = 1

try:
    _ANTIALIASING = QPainter.RenderHint.Antialiasing
except AttributeError:  # Qt 5 bindings expose the unscoped enum
    _ANTIALIASING = QPainter.Antialiasing

try:
    _TEXT_WORD_WRAP = Qt.TextFlag.TextWordWrap
except AttributeError:  # Qt 5 bindings expose the unscoped enum
    _TEXT_WORD_WRAP = Qt.TextWordWrap



def _as_color(value) -> QColor:
    """Return `value` as a `QColor`, accepting names, QColor and RGB(A) tuples."""
    try:
        if isinstance(value, QColor):
            return QColor(value)
        if isinstance(value, (tuple, list)):
            return QColor(*value)
        return QColor(value)
    except Exception:
        return QColor()


class _CommentTextItem(QGraphicsTextItem):
    """The inline plain-text editor/rendering child of a :class:`Comment`."""

    def __init__(self, comment: "Comment") -> None:
        super().__init__(comment)
        self._comment = comment
        self.document().setDocumentMargin(0)

    def keyPressEvent(self, event) -> None:
        """Handle Escape (cancel) and Ctrl+Enter (commit), then edit normally."""
        if event.key() == Qt.Key.Key_Escape:
            self._comment.cancel_edit()
            event.accept()
            return
        if (
            event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter)
            and event.modifiers() & Qt.KeyboardModifier.ControlModifier
        ):
            self._comment.finish_edit()
            event.accept()
            return
        super().keyPressEvent(event)

    def focusOutEvent(self, event) -> None:
        """Commit the text when the editor loses focus."""
        super().focusOutEvent(event)
        self._comment._on_editor_focus_out()


class Comment(Serializable, QGraphicsRectItem):
    """A movable, selectable, inline-editable note on the canvas.

    The note auto-sizes: its width is the requested width, and its height grows
    to fit the wrapped text, never below :attr:`MIN_HEIGHT`. Use
    :meth:`setSize` to change the requested size. The whole body is draggable,
    so a separate header is unnecessary.

    :param scene: the scene the comment belongs to
    :param text: initial multi-line plain text
    :param x: initial x position in scene coordinates
    :param y: initial y position in scene coordinates
    :param width: requested outer width; clamped to :attr:`MIN_WIDTH`
    :param height: requested outer height; clamped to :attr:`MIN_HEIGHT`
    """

    #: Smallest width a note may have, in scene units.
    MIN_WIDTH = 140.0
    #: Smallest height a note may have, in scene units.
    MIN_HEIGHT = 60.0
    #: Default width used by :meth:`Scene.addComment`.
    DEFAULT_WIDTH = 220.0
    #: Default height used by :meth:`Scene.addComment`.
    DEFAULT_HEIGHT = 100.0
    #: Neutral default background colour ``(r, g, b, a)``.
    DEFAULT_BACKGROUND = (255, 248, 214, 232)
    #: Neutral default border colour ``(r, g, b, a)``.
    DEFAULT_BORDER = (190, 175, 120, 255)
    #: Neutral default text colour ``(r, g, b, a)``.
    DEFAULT_TEXT = (35, 35, 35, 255)
    #: Gap between the frame and the text, in scene units.
    PADDING = 10.0
    #: z-value used by notes that have not been brought forward or sent back.
    DEFAULT_Z_VALUE = 1.0
    #: Corner radius of the painted frame.
    CORNER_RADIUS = 6.0

    def __init__(
        self,
        scene: "Scene",
        text: str = "",
        x: float = 0,
        y: float = 0,
        width: float = DEFAULT_WIDTH,
        height: float = DEFAULT_HEIGHT,
    ) -> None:
        QGraphicsRectItem.__init__(self, 0, 0, width, height)
        Serializable.__init__(self)

        self.scene: Scene = scene
        self._requested_width = max(float(width), self.MIN_WIDTH)
        self._requested_height = max(float(height), self.MIN_HEIGHT)
        self._text = str(text or "")

        self._background_color = QColor(*self.DEFAULT_BACKGROUND)
        self._border_color = QColor(*self.DEFAULT_BORDER)
        self._text_color = QColor(*self.DEFAULT_TEXT)
        self._border_width = 1.0

        self._editing = False
        self._edit_original_text = ""
        self._drag_start_pos: object | None = None
        self._disposed = False

        self._text_item = _CommentTextItem(self)
        self._text_item.setDefaultTextColor(self._text_color)
        self._text_item.setTextInteractionFlags(
            Qt.TextInteractionFlag.NoTextInteraction
        )
        self._text_item.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self._text_item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsFocusable, False)
        self._text_item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        self._text_item.setPlainText(self._text)
        self._text_item.document().contentsChanged.connect(
            self._on_editor_contents_changed
        )

        self.setPos(x, y)
        self.setZValue(self.DEFAULT_Z_VALUE)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.CursorShape.ArrowCursor)

        self._update_geometry()

        # Register with the scene. The guard keeps deserialization safe when a
        # caller has already attached the item by hand.
        if self not in self.scene.comments:
            self.scene.addComment(self)
        try:
            if self not in self.scene.grScene.items():
                self.scene.grScene.addItem(self)
        except Exception:
            try:
                self.scene.grScene.addItem(self)
            except Exception:
                pass

    # ------------------------------------------------------------------
    # text
    # ------------------------------------------------------------------
    def text(self) -> str:
        """Return the note's plain text, including in-progress editor text."""
        if self._editing:
            return self._text_item.toPlainText()
        return self._text

    def setText(self, text: str, store_history: bool = False) -> bool:
        """Replace the note's plain text.

        The note grows to fit the new text. The scene is marked modified when
        the text changes; a history entry is stored only when `store_history`
        is ``True``.

        :param text: new multi-line plain text
        :param store_history: store an ``"Edited comment"`` history entry
        :return: ``True`` when the text changed
        """
        text = str(text or "")
        if self._editing:
            self.finish_edit(commit=False, store_history=False)
        if text == self._text:
            return False
        self._set_text(text)
        self._mark_modified("Edited comment", store_history)
        return True

    def _set_text(self, text: str) -> None:
        """Apply text without touching history or the modified flag."""
        self._text = str(text or "")
        self._text_item.setPlainText(self._text)
        self._update_geometry()

    def _mark_modified(self, desc: str, store_history: bool) -> None:
        try:
            self.scene.has_been_modified = True
        except Exception:
            pass
        if store_history:
            try:
                self.scene.history.storeHistory(desc, setModified=True)
            except Exception:
                pass

    # ------------------------------------------------------------------
    # size and geometry
    # ------------------------------------------------------------------
    def setSize(self, width: float, height: float) -> None:
        """Set the requested outer size, clamped to the minimum.

        The actual height may be larger when the text needs more room.

        :param width: requested width in scene units
        :param height: requested height in scene units
        """
        self._requested_width = max(float(width), self.MIN_WIDTH)
        self._requested_height = max(float(height), self.MIN_HEIGHT)
        self._update_geometry()
        try:
            self.scene.has_been_modified = True
        except Exception:
            pass

    def resize(self, width: float, height: float) -> None:
        """Alias of :meth:`setSize`."""
        self.setSize(width, height)

    def _update_geometry(self) -> None:
        """Wrap the text at the current width and grow the height to fit it."""
        try:
            width = max(float(self._requested_width), float(self.MIN_WIDTH))
            text_width = max(width - 2.0 * float(self.PADDING), 1.0)
            self._text_item.setTextWidth(text_width)
            text_height = float(self._text_item.boundingRect().height())
            height = max(
                float(self._requested_height),
                float(self.MIN_HEIGHT),
                text_height + 2.0 * float(self.PADDING),
            )
            self.setRect(0, 0, width, height)
            self._text_item.setPos(float(self.PADDING), float(self.PADDING))
            self.update()
        except Exception:
            dumpException()

    def _on_editor_contents_changed(self) -> None:
        """Grow the frame while the inline editor is being typed into."""
        if self._editing:
            self._update_geometry()

    # ------------------------------------------------------------------
    # inline editing
    # ------------------------------------------------------------------
    def is_editing(self) -> bool:
        """Return whether the inline editor is currently open."""
        return self._editing

    def editor(self) -> QGraphicsTextItem:
        """Return the inline text item, for apps that want to customise it."""
        return self._text_item

    def begin_edit(self) -> bool:
        """Open the inline editor and give it keyboard focus.

        Existing text is selected so typing replaces it, matching a text field.
        Returns ``False`` when the note is already being edited or disposed.
        """
        if self._editing or self._disposed:
            return False
        self._editing = True
        self._edit_original_text = self._text
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        self._text_item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsFocusable, True)
        self._text_item.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)
        self._text_item.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextEditorInteraction
        )
        try:
            cursor = self._text_item.textCursor()
            cursor.select(QTextCursor.SelectionType.Document)
            self._text_item.setTextCursor(cursor)
        except Exception:
            pass
        self._text_item.setFocus()
        self.update()
        return True

    def finish_edit(self, commit: bool = True, store_history: bool = True) -> bool:
        """End the inline edit.

        :param commit: ``True`` keeps the editor's text, ``False`` restores the
            text the note had when :meth:`begin_edit` was called
        :param store_history: store an ``"Edited comment"`` history entry when
            committing changed text
        :return: ``True`` when committed text differs from the original text
        """
        if not self._editing:
            return False
        self._editing = False
        original = self._edit_original_text
        new_text = self._text_item.toPlainText() if commit else original
        changed = bool(commit and new_text != original)

        self._text = new_text
        self._text_item.setPlainText(new_text)
        self._update_geometry()
        self._leave_editor_mode()

        if changed:
            self._mark_modified("Edited comment", store_history)
        return changed

    def cancel_edit(self, store_history: bool = False) -> None:
        """Cancel the inline edit and restore the pre-edit text.

        `store_history` is accepted for symmetry with :meth:`finish_edit` but
        cancelling never stores a history entry.
        """
        self.finish_edit(commit=False, store_history=store_history)

    def _leave_editor_mode(self) -> None:
        """Disable the editor and restore mouse-dragging of the note."""
        try:
            self._text_item.setTextInteractionFlags(
                Qt.TextInteractionFlag.NoTextInteraction
            )
        except Exception:
            pass
        try:
            self._text_item.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        except Exception:
            pass
        try:
            self._text_item.setFlag(
                QGraphicsItem.GraphicsItemFlag.ItemIsFocusable, False
            )
        except Exception:
            pass
        try:
            self._text_item.clearFocus()
        except Exception:
            pass
        if not self._disposed:
            try:
                self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
            except Exception:
                pass
        self.update()

    def _on_editor_focus_out(self) -> None:
        """Commit when focus leaves the editor without an explicit cancel."""
        if self._editing and not self._disposed:
            self.finish_edit(commit=True, store_history=True)

    # ------------------------------------------------------------------
    # colours
    # ------------------------------------------------------------------
    def backgroundColor(self) -> QColor:
        """Return the current background colour."""
        return QColor(self._background_color)

    def borderColor(self) -> QColor:
        """Return the current border colour."""
        return QColor(self._border_color)

    def textColor(self) -> QColor:
        """Return the current text colour."""
        return QColor(self._text_color)

    def setBackgroundColor(self, color) -> bool:
        """Set the background colour from a QColor, colour name or RGBA tuple."""
        c = _as_color(color)
        if not c.isValid() or c == self._background_color:
            return False
        self._background_color = c
        self._mark_modified("Recolored comment", False)
        self.update()
        return True

    def setBorderColor(self, color) -> bool:
        """Set the border colour from a QColor, colour name or RGBA tuple."""
        c = _as_color(color)
        if not c.isValid() or c == self._border_color:
            return False
        self._border_color = c
        self._mark_modified("Recolored comment", False)
        self.update()
        return True

    def setTextColor(self, color) -> bool:
        """Set the text colour from a QColor, colour name or RGBA tuple."""
        c = _as_color(color)
        if not c.isValid() or c == self._text_color:
            return False
        self._text_color = c
        try:
            self._text_item.setDefaultTextColor(c)
        except Exception:
            pass
        self._mark_modified("Recolored comment", False)
        self.update()
        return True

    def setColors(
        self,
        background=None,
        border=None,
        text=None,
    ) -> bool:
        """Set any of the three colours; arguments left as ``None`` stay put."""
        changed = False
        if background is not None:
            changed = self.setBackgroundColor(background) or changed
        if border is not None:
            changed = self.setBorderColor(border) or changed
        if text is not None:
            changed = self.setTextColor(text) or changed
        return changed

    # ------------------------------------------------------------------
    # stacking order
    # ------------------------------------------------------------------
    def bringToFront(self) -> None:
        """Put the note above every other item in the scene."""
        try:
            top = max(
                (item.zValue() for item in self.scene.grScene.items()),
                default=self.DEFAULT_Z_VALUE,
            )
            self.setZValue(float(top) + 1.0)
        except Exception:
            self.setZValue(self.zValue() + 1.0)

    def sendToBack(self) -> None:
        """Put the note below every other item in the scene."""
        try:
            bottom = min(
                (item.zValue() for item in self.scene.grScene.items()),
                default=self.DEFAULT_Z_VALUE,
            )
            self.setZValue(float(bottom) - 1.0)
        except Exception:
            self.setZValue(self.zValue() - 1.0)

    def resetZValue(self) -> None:
        """Return the note to the default canvas order."""
        self.setZValue(self.DEFAULT_Z_VALUE)

    # ------------------------------------------------------------------
    # removal
    # ------------------------------------------------------------------
    def dispose(self) -> None:
        """Remove the note from the graphics scene and the scene's list."""
        if self._disposed:
            return
        if self._editing:
            self.finish_edit(commit=False, store_history=False)
        self._disposed = True
        try:
            if self.scene.grScene is not None and self in self.scene.grScene.items():
                self.scene.grScene.removeItem(self)
        except Exception:
            pass
        try:
            self.scene.removeComment(self)
        except Exception:
            pass

    def remove(self) -> None:
        """Remove the note from the scene. The caller owns the history entry."""
        self.dispose()

    # ------------------------------------------------------------------
    # interaction
    # ------------------------------------------------------------------
    def mousePressEvent(self, event) -> None:
        """Start tracking a drag so a real move can be added to history."""
        if self._editing:
            event.ignore()
            return
        self._drag_start_pos = self.pos()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        """Store a history entry when the note was actually dragged."""
        super().mouseReleaseEvent(event)
        start = self._drag_start_pos
        self._drag_start_pos = None
        if start is not None and not self._editing:
            try:
                if self.pos() != start:
                    self.scene.history.storeHistory("Moved comment", setModified=True)
            except Exception:
                pass

    def mouseDoubleClickEvent(self, event) -> None:
        """Open the inline editor on a double click."""
        if not self._editing and event.button() == Qt.MouseButton.LeftButton:
            self.begin_edit()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    def contextMenuEvent(self, event) -> None:
        """Offer editing, stacking and deletion from the note's context menu."""
        if self._editing:
            event.ignore()
            return
        menu = QMenu()
        edit_act = menu.addAction("Edit…")
        front_act = menu.addAction("Bring to Front")
        back_act = menu.addAction("Send to Back")
        reset_act = menu.addAction("Reset Order")
        menu.addSeparator()
        delete_act = menu.addAction("Delete Comment")
        try:
            action = menu.exec(event.screenPos())
        except Exception:
            action = None
        if action == edit_act:
            self.begin_edit()
        elif action == front_act:
            self.bringToFront()
            self._mark_modified("Reordered comment", True)
        elif action == back_act:
            self.sendToBack()
            self._mark_modified("Reordered comment", True)
        elif action == reset_act:
            self.resetZValue()
            self._mark_modified("Reordered comment", True)
        elif action == delete_act:
            self.remove()
            try:
                self.scene.history.storeHistory("Deleted comment", setModified=True)
            except Exception:
                pass

    def paint(self, painter: QPainter, option, widget=None) -> None:
        """Paint the note frame, selection outline and empty-note hint."""
        try:
            painter.setRenderHint(_ANTIALIASING, True)
            rect = self.rect()
            painter.setPen(QPen(self._border_color, self._border_width))
            painter.setBrush(QBrush(self._background_color))
            painter.drawRoundedRect(rect, self.CORNER_RADIUS, self.CORNER_RADIUS)

            if self.isSelected():
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.setPen(QPen(QColor(70, 130, 220), 2.0))
                painter.drawRoundedRect(
                    rect.adjusted(1, 1, -1, -1),
                    self.CORNER_RADIUS,
                    self.CORNER_RADIUS,
                )

            if not self._text and not self._editing:
                inner = rect.adjusted(
                    self.PADDING, self.PADDING, -self.PADDING, -self.PADDING
                )
                painter.setPen(QPen(QColor(120, 120, 120)))
                painter.setFont(self._text_item.font())
                flags = int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
                flags |= int(_TEXT_WORD_WRAP)
                painter.drawText(inner, flags, "Double-click to edit")
        except Exception:
            dumpException()

    # ------------------------------------------------------------------
    # serialization
    # ------------------------------------------------------------------
    def serialize(self) -> dict:
        """Return the note as the JSON-ready dictionary documented in the module."""
        try:
            p = self.pos()
            r = self.rect()
        except Exception:
            p = None
            r = None
        return {
            "id": self.id,
            "type": "Comment",
            "version": COMMENT_SERIALIZATION_VERSION,
            "text": self.text(),
            "x": p.x() if p is not None else 0.0,
            "y": p.y() if p is not None else 0.0,
            "w": r.width() if r is not None else self.DEFAULT_WIDTH,
            "h": r.height() if r is not None else self.DEFAULT_HEIGHT,
            "z": float(self.zValue()),
            "style": {
                "background": self._background_color.getRgb(),
                "border": self._border_color.getRgb(),
                "text": self._text_color.getRgb(),
            },
        }

    def deserialize(
        self,
        data: dict,
        hashmap: dict | None = None,
        restore_id: bool = True,
    ) -> bool:
        """Restore the note from :meth:`serialize` output.

        Missing ``style`` or ``z`` keys fall back to the neutral defaults, so a
        minimal hand-written comment payload loads too.

        :param data: serialized comment
        :param hashmap: optional id-to-object map, matching other deserializers
        :param restore_id: restore the id stored in the file
        :return: ``True`` when the note was restored
        """
        try:
            if self._editing:
                self.finish_edit(commit=False, store_history=False)
            if restore_id and "id" in data:
                self.id = data["id"]
                if hashmap is not None:
                    hashmap[self.id] = self

            self._set_text(data.get("text", ""))
            try:
                self.setPos(float(data.get("x", 0.0)), float(data.get("y", 0.0)))
            except Exception:
                pass
            try:
                width = float(data.get("w", data.get("width", self.DEFAULT_WIDTH)))
                height = float(data.get("h", data.get("height", self.DEFAULT_HEIGHT)))
            except Exception:
                width = self.DEFAULT_WIDTH
                height = self.DEFAULT_HEIGHT
            self._requested_width = max(width, self.MIN_WIDTH)
            self._requested_height = max(height, self.MIN_HEIGHT)
            self._update_geometry()

            try:
                self.setZValue(float(data.get("z", self.DEFAULT_Z_VALUE)))
            except Exception:
                self.setZValue(self.DEFAULT_Z_VALUE)

            style = data.get("style", {})
            if not isinstance(style, dict):
                style = {}
            background = style.get("background", self.DEFAULT_BACKGROUND)
            border = style.get("border", self.DEFAULT_BORDER)
            text = style.get("text", self.DEFAULT_TEXT)
            self._background_color = (
                QColor(*background)
                if isinstance(background, (list, tuple))
                else QColor(*self.DEFAULT_BACKGROUND)
            )
            self._border_color = (
                QColor(*border)
                if isinstance(border, (list, tuple))
                else QColor(*self.DEFAULT_BORDER)
            )
            self._text_color = (
                QColor(*text)
                if isinstance(text, (list, tuple))
                else QColor(*self.DEFAULT_TEXT)
            )
            try:
                self._text_item.setDefaultTextColor(self._text_color)
            except Exception:
                pass
            self.update()
            return True
        except Exception as e:
            dumpException(e)
            return False
