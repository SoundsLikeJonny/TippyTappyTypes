#      TippyTappyTypes is a minimal typing test software that sits in the corner of your screen while you work!
#      Copyright (C) 2026 Jon Evans
#
#      This program is free software: you can redistribute it and/or modify
#      it under the terms of the GNU General Public License as published by
#      the Free Software Foundation, either version 3 of the License, or
#      (at your option) any later version.
#
#      This program is distributed in the hope that it will be useful,
#      but WITHOUT ANY WARRANTY; without even the implied warranty of
#      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#      GNU General Public License for more details.
#
#      You should have received a copy of the GNU General Public License
#      along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""A tiny always-on-top window holding only the animated character.

It sits immediately to the left of the typing overlay, touching it, and stays
on screen when the overlay is hidden so the user has something to click to
bring the overlay back.
"""

import os
from typing import List, Optional

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer, Signal, QPoint, QRect, QSize
from PySide6.QtGui import QPainter, QPixmap, QColor

from project_info import resource_path
from src.config import Config


class CharacterWindow(QWidget):
    """Frameless window that draws only the character animation.

    The window is sized to the animation frame so it has no padding, and it
    never takes focus so clicking it cannot pull focus away from whatever the
    user is typing in.
    """

    clicked: Signal = Signal()

    def __init__(self, config: Config) -> None:
        super().__init__(None)
        self.config = config
        self._frames: List[QPixmap] = []
        self._anim_index: int = 0
        self._idle_phase: int = 0
        self._active: bool = False
        self._press_pos: Optional[QPoint] = None

        self._load_frames()
        self._setup_window()

        self._idle_timer = QTimer(self)
        self._idle_timer.setInterval(300)
        self._idle_timer.timeout.connect(self._on_idle_tick)
        self._idle_timer.start()

        self._render()

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def _setup_window(self) -> None:
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setFocusPolicy(Qt.NoFocus)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip("Click to show or hide the typing window")
        self.setFixedSize(self._canvas_size())

    def _load_frames(self) -> None:
        """Load the same typing animation frames the overlay uses."""
        base = resource_path("resources/anims/status")
        for i in range(1, 5):
            path = os.path.join(base, f"typing_{i:02d}.PNG")
            if not os.path.exists(path):
                print(f"WARNING: character frame not found: {path}")
                continue
            pix = QPixmap(path)
            if pix.isNull():
                print(f"WARNING: character frame failed to load: {path}")
                continue
            self._frames.append(pix)

    def _canvas_size(self) -> QSize:
        """Frame size plus the 4px the idle bob needs below the character."""
        if not self._frames:
            return QSize(24, 24)
        frame = self._frames[0]
        return QSize(frame.width(), frame.height() + 4)

    # ------------------------------------------------------------------
    # Painting
    # ------------------------------------------------------------------

    def _tint_pixmap(self, pix: QPixmap, color: str) -> QPixmap:
        """Recolor a pixmap to the given color, preserving its alpha shape."""
        tinted = QPixmap(pix.size())
        tinted.fill(Qt.transparent)
        p = QPainter(tinted)
        p.drawPixmap(0, 0, pix)
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        p.fillRect(tinted.rect(), QColor(color))
        p.end()
        return tinted

    def _render(self) -> None:
        """Rebuild the pixmap for the current frame and animation state."""
        if not self._frames:
            return
        color = self.config.get("typed_color", "#8b047e")
        if self._active:
            frame = self._frames[self._anim_index % len(self._frames)]
            self._pixmap = self._tint_pixmap(frame, color)
        else:
            frame = self._frames[0]
            offset = 2 if self._idle_phase else 0
            canvas = QPixmap(frame.width(), frame.height() + 4)
            canvas.fill(Qt.transparent)
            p = QPainter(canvas)
            p.drawPixmap(0, offset, frame)
            p.end()
            self._pixmap = self._tint_pixmap(canvas, color)
        self.update()

    def paintEvent(self, event) -> None:
        pixmap = getattr(self, "_pixmap", None)
        if pixmap is None:
            return
        painter = QPainter(self)
        painter.drawPixmap(0, 0, pixmap)

    # ------------------------------------------------------------------
    # Animation
    # ------------------------------------------------------------------

    def set_active(self, active: bool) -> None:
        """Switch between the typing animation and the idle bob."""
        if self._active == active:
            return
        self._active = active
        self._render()

    def advance(self) -> None:
        """Step to the next typing frame (called on each typed character)."""
        if not self._frames:
            return
        self._anim_index = (self._anim_index + 1) % len(self._frames)
        if self._active:
            self._render()

    def _on_idle_tick(self) -> None:
        if self._active or not self._frames:
            return
        self._idle_phase = 1 - self._idle_phase
        self._render()

    def apply_theme(self) -> None:
        """Re-tint the character after a theme or color change."""
        self._render()

    # ------------------------------------------------------------------
    # Placement
    # ------------------------------------------------------------------

    def align_to(self, overlay_rect: QRect) -> None:
        """Place this window immediately left of the overlay, vertically centered."""
        x = overlay_rect.x() - self.width()
        y = overlay_rect.y() + (overlay_rect.height() - self.height()) // 2
        self.move(x, y)

    def overlay_position(self, overlay_size: QSize) -> QPoint:
        """Top-left the overlay needs so it touches this window's right edge."""
        x = self.x() + self.width()
        y = self.y() - (overlay_size.height() - self.height()) // 2
        return QPoint(x, y)

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self._press_pos = event.position().toPoint()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.LeftButton and self._press_pos is not None:
            moved = (event.position().toPoint() - self._press_pos).manhattanLength()
            self._press_pos = None
            if moved <= 4:
                self.clicked.emit()
            event.accept()
            return
        super().mouseReleaseEvent(event)
