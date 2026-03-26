from typing import Optional
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, Property, QRectF
from PySide6.QtGui import QColor, QPainter, QPen, QBrush
from PySide6.QtWidgets import QWidget, QPushButton, QFrame, QHBoxLayout, QVBoxLayout, QLabel

class AnimatedMicWidget(QWidget):
    """Modernized mic widget with subtle Indigo pulse."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setFixedSize(140, 140)
        self._recording = False
        self._pulse_value = 0.0
        self._animation = QPropertyAnimation(self, b"pulseValue")
        self._animation.setDuration(1200)
        self._animation.setStartValue(0.0)
        self._animation.setEndValue(1.0)
        self._animation.setEasingCurve(QEasingCurve.InOutQuad)
        self._animation.setLoopCount(-1)

    @Property(float)
    def pulseValue(self) -> float:
        return self._pulse_value

    @pulseValue.setter
    def pulseValue(self, value: float) -> None:
        self._pulse_value = value
        self.update()

    def set_recording(self, recording: bool) -> None:
        self._recording = recording
        if recording:
            self._animation.start()
        else:
            self._animation.stop()
            self._pulse_value = 0.0
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        center = self.rect().center()
        
        # New palette colors
        primary = QColor("#4F46E5") # Indigo 600
        recording_accent = QColor("#EF4444") # Red 500
        
        base_radius = 50

        if self._recording:
            # Subtle red pulse when recording
            scale = 1.0 + (0.2 * self._pulse_value)
            radius = base_radius * scale
            color = recording_accent
            glow_color = recording_accent
        else:
            radius = base_radius
            color = primary
            glow_color = primary

        # Draw soft glow
        for i in range(2):
            alpha = 20 - (i * 10)
            glow = QColor(glow_color)
            glow.setAlpha(alpha)
            painter.setPen(Qt.NoPen)
            painter.setBrush(glow)
            painter.drawEllipse(center, radius + (i * 15), radius + (i * 15))

        # Main circle with subtle shadow/border appearance
        painter.setBrush(color)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(center, radius, radius)

        # Draw minimalist mic icon
        painter.setBrush(Qt.white)
        # Main mic body
        mic_w = 16
        mic_h = 24
        painter.drawRoundedRect(center.x() - mic_w/2, center.y() - 15, mic_w, mic_h, 8, 8)
        
        # Mic stand
        painter.setPen(QPen(Qt.white, 3, Qt.SolidLine, Qt.RoundCap))
        painter.setBrush(Qt.NoBrush)
        painter.drawArc(center.x() - 14, center.y() - 8, 28, 20, 180 * 16, 180 * 16)
        painter.drawLine(center.x(), center.y() + 12, center.x(), center.y() + 20)
        painter.drawLine(center.x() - 8, center.y() + 20, center.x() + 8, center.y() + 20)


class NavButton(QPushButton):
    """Updated NavButton with higher spacing and simpler labels."""

    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        self.setText(text)
        self.setCheckable(True)
        self.setFixedHeight(48)
        self.setCursor(Qt.PointingHandCursor)


class FolderCard(QFrame):
    """Modern Slate Folder View."""

    clicked = Signal(str)

    def __init__(self, title: str, count: int, icon_char: str = "📁", parent=None):
        super().__init__(parent)
        self.title = title
        self.setObjectName("CardShadow")
        self.setCursor(Qt.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Leading Icon
        icon_label = QLabel(icon_char)
        icon_label.setStyleSheet("font-size: 24px; background: transparent;")
        layout.addWidget(icon_label)

        # Text
        txt_layout = QVBoxLayout()
        txt_layout.setSpacing(2)
        
        title_label = QLabel(title)
        title_label.setObjectName("SectionTitle")
        
        self.count_label = QLabel(f"{count} Dictations")
        self.count_label.setStyleSheet("font-size: 12px; color: #64748B;")
        
        txt_layout.addWidget(title_label)
        txt_layout.addWidget(self.count_label)
        layout.addLayout(txt_layout, 1)

    def mousePressEvent(self, event) -> None:
        self.clicked.emit(self.title)
        super().mousePressEvent(event)


class RecordingCard(QFrame):
    """Sleek Session Summary Card."""

    clicked = Signal(str)

    def __init__(self, title: str, time_ago: str, duration: str, status: str, session_path: str = "", parent=None):
        super().__init__(parent)
        self.session_path = session_path
        self.setObjectName("CardShadow")
        self.setCursor(Qt.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        head = QHBoxLayout()
        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: 700; font-size: 14px; color: #0F172A;")
        head.addWidget(title_label, 1)
        
        status_pill = QLabel(status)
        status_pill.setObjectName("StatusPill")
        color = "#10B981" if status == "Transcribed" else "#F59E0B"
        bg = "#D1FAE5" if status == "Transcribed" else "#FEF3C7"
        status_pill.setStyleSheet(f"background-color: {bg}; color: {color}; border-radius: 6px; padding: 2px 8px;")
        head.addWidget(status_pill)
        layout.addLayout(head)

        meta = QHBoxLayout()
        time_lbl = QLabel(f"🕒 {time_ago}")
        dur_lbl = QLabel(f"⏱ {duration}")
        for lbl in (time_lbl, dur_lbl):
            lbl.setStyleSheet("font-size: 11px; color: #64748B;")
            meta.addWidget(lbl)
        meta.addStretch()
        layout.addLayout(meta)

    def mousePressEvent(self, event) -> None:
        self.clicked.emit(self.session_path)
        super().mousePressEvent(event)
