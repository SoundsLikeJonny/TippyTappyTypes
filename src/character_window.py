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

# The character is drawn at this fraction of the window height, so it sits
# inside the strip with a little breathing room instead of filling it edge to
# edge. The window width follows the same fraction.
CHARACTER_SCALE: float = 0.75


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
        # Width is fixed to the frame; the height is set to match the overlay
        # in align_to(), so only a minimum is fixed here.
        self.setFixedWidth(self._canvas_size().width())
        self.setMinimumHeight(self._canvas_size().height())

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
        self._content_rect = self._compute_content_rect()

    def _compute_content_rect(self) -> QRect:
        """Union of the non-transparent bounds across every frame.

        The PNGs carry transparent padding, so scaling the raw frame would
        leave the character smaller than the window. Cropping to this rect
        first makes the character itself fill the window height, and using the
        union across frames keeps the animation from jittering.
        """
        if not self._frames:
            return QRect()
        union: Optional[QRect] = None
        for pix in self._frames:
            img = pix.toImage()
            w, h = img.width(), img.height()
            rows = [y for y in range(h)
                    if any(img.pixelColor(x, y).alpha() > 0 for x in range(w))]
            cols = [x for x in range(w)
                    if any(img.pixelColor(x, y).alpha() > 0 for y in range(h))]
            if not rows or not cols:
                continue
            bounds = QRect(cols[0], rows[0],
                           cols[-1] - cols[0] + 1, rows[-1] - rows[0] + 1)
            union = bounds if union is None else union.united(bounds)
        if union is None:
            return self._frames[0].rect()
        return union

    def _canvas_size(self) -> QSize:
        """Natural size of the cropped character."""
        rect = getattr(self, "_content_rect", None)
        if rect is None or rect.isEmpty():
            if not self._frames:
                return QSize(24, 24)
            return self._frames[0].size()
        return QSize(rect.width(), rect.height())

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
        else:
            frame = self._frames[0]
        rect = getattr(self, "_content_rect", None)
        if rect is not None and not rect.isEmpty():
            frame = frame.copy(rect)
        self._pixmap = self._tint_pixmap(frame, color)
        self.update()

    def paintEvent(self, event) -> None:
        pixmap = getattr(self, "_pixmap", None)
        if pixmap is None or pixmap.isNull():
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        # Draw the character at CHARACTER_SCALE of the window height, keeping
        # its aspect ratio, centred horizontally and vertically. The window
        # width is derived from the same scale in align_to(), so the character
        # fills it exactly.
        target_h = max(1, round(self.height() * CHARACTER_SCALE))
        if pixmap.height() <= 0:
            return
        # Idle bob: nudge the character down a pixel on alternate ticks.
        bob = 1 if (not self._active and self._idle_phase) else 0
        draw_h = max(1, target_h - bob)
        target_w = max(1, round(pixmap.width() * draw_h / pixmap.height()))
        x = (self.width() - target_w) // 2
        y = (self.height() - target_h) // 2 + bob
        painter.drawPixmap(
            QRect(x, y, target_w, draw_h),
            pixmap,
            pixmap.rect(),
        )

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
        """Match the overlay's height and sit immediately left of it.

        The character is scaled to the overlay's full height, so the window
        width follows the frame's aspect ratio at that height.
        """
        if overlay_rect.height() > 0:
            target_h = overlay_rect.height()
            if self.height() != target_h:
                self.setFixedHeight(target_h)
            target_w = self._scaled_width(target_h)
            if self.width() != target_w:
                self.setFixedWidth(target_w)
        x = overlay_rect.x() - self.width()
        y = overlay_rect.y()
        self.move(x, y)

    def _scaled_width(self, height: int) -> int:
        """Window width that keeps the character's aspect ratio at `height`."""
        rect = getattr(self, "_content_rect", None)
        if rect is None or rect.isEmpty() or height <= 0:
            return self._canvas_size().width()
        draw_h = max(1, round(height * CHARACTER_SCALE))
        return max(1, round(rect.width() * draw_h / rect.height()))

    def overlay_position(self, overlay_size: QSize) -> QPoint:
        """Top-left the overlay needs so it touches this window's right edge."""
        return QPoint(self.x() + self.width(), self.y())

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
