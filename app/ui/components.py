from typing import Optional
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, Property, QRectF
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget, QPushButton, QFrame, QHBoxLayout, QVBoxLayout, QLabel

class AnimatedMicWidget(QWidget):
    """Animated microphone widget with pulse effect."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setFixedSize(120, 120)  # Smaller size to prevent overlap
        self._recording = False
        self._pulse_value = 0.0
        self._animation = QPropertyAnimation(self, b"pulseValue")
        self._animation.setDuration(1000)
        self._animation.setStartValue(0.0)
        self._animation.setEndValue(1.0)
        self._animation.setEasingCurve(QEasingCurve.InOutSine)
        self._animation.setLoopCount(-1)

    def get_pulse_value(self) -> float:
        return self._pulse_value

    def set_pulse_value(self, value: float) -> None:
        self._pulse_value = value
        self.update()

    pulseValue = Property(float, get_pulse_value, set_pulse_value)

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

        # Background circle
        center = self.rect().center()
        base_radius = 45  # Smaller radius for 120x120 widget

        if self._recording:
            # Pulsing effect when recording
            scale = 1.0 + (0.15 * self._pulse_value)
            radius = base_radius * scale
            color = QColor("#E5A54B")  # Orange accent for recording
            glow_color = QColor("#E5A54B")
        else:
            radius = base_radius
            color = QColor("#0B8E99")  # Teal primary
            glow_color = QColor("#0B8E99")

        # Draw glow
        painter.setBrush(Qt.NoBrush)
        for i in range(3):
            alpha = 30 - (i * 10)
            glow = QColor(glow_color)
            glow.setAlpha(alpha)
            painter.setPen(QPen(glow, 3))
            painter.drawEllipse(center, radius + (i * 8), radius + (i * 8))

        # Draw main circle
        painter.setBrush(color)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(center, radius, radius)

        # Draw microphone icon
        painter.setBrush(Qt.white)
        mic_width = 18
        mic_height = 28
        mic_rect = QRectF(
            center.x() - mic_width / 2,
            center.y() - mic_height / 2 - 5,
            mic_width,
            mic_height,
        )
        painter.drawRoundedRect(mic_rect, 9, 9)

        # Mic stand
        stand_width = 6
        stand_height = 14
        stand_rect = QRectF(
            center.x() - stand_width / 2,
            center.y() + 8,
            stand_width,
            stand_height,
        )
        painter.drawRoundedRect(stand_rect, 3, 3)

        # Mic base
        base_width = 24
        base_height = 3
        painter.drawRoundedRect(
            center.x() - base_width / 2,
            center.y() + 20,
            base_width,
            base_height,
            2,
            2,
        )


class NavButton(QPushButton):
    """Custom navigation button with icon and text."""

    def __init__(self, text: str, icon_text: str, parent=None):
        super().__init__(parent)
        self.setText(text)
        self._icon_text = icon_text
        self.setCheckable(True)
        self.setFixedHeight(56)
        self.setCursor(Qt.PointingHandCursor)


class FolderCard(QFrame):
    """Folder card widget."""

    clicked = Signal(str)

    def __init__(self, title: str, count: int, color: str, parent=None):
        super().__init__(parent)
        self.title = title
        self._setup_ui(title, count, color)

    def _setup_ui(self, title: str, count: int, color: str) -> None:
        self.setObjectName("FolderCard")
        self.setCursor(Qt.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Icon
        icon = QFrame()
        icon.setFixedSize(56, 56)
        icon.setStyleSheet(
            f"background-color: {color}; border-radius: 14px; "
            "border: 2px solid rgba(255, 255, 255, 0.5);"
        )
        layout.addWidget(icon)

        # Text content
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)

        title_label = QLabel(title)
        title_label.setStyleSheet(
            "font-size: 16px; font-weight: 600; color: #0F172A; "
            "letter-spacing: -0.2px;"
        )

        self.count_label = QLabel(f"{count} recordings")
        self.count_label.setStyleSheet(
            "font-size: 13px; color: #64748B; font-weight: 500;"
        )

        text_layout.addWidget(title_label)
        text_layout.addWidget(self.count_label)
        layout.addLayout(text_layout, 1)

        # Arrow
        arrow = QLabel("›")
        arrow.setStyleSheet("font-size: 24px; color: #BDBDBD;")
        layout.addWidget(arrow)

    def update_count(self, count: int) -> None:
        self.count_label.setText(f"{count} recordings")

    def mousePressEvent(self, event) -> None:
        self.clicked.emit(self.title)
        super().mousePressEvent(event)


class RecordingCard(QFrame):
    """Recent recording card."""

    clicked = Signal(str)

    def __init__(
        self,
        title: str,
        time_ago: str,
        duration: str,
        status: str,
        session_path: Optional[str] = None,
        parent=None,
    ):
        super().__init__(parent)
        self.session_path = session_path or ""
        self._setup_ui(title, time_ago, duration, status)

    def _setup_ui(self, title: str, time_ago: str, duration: str, status: str) -> None:
        self.setObjectName("RecordingCard")
        self.setCursor(Qt.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet(
            "font-size: 15px; font-weight: 600; color: #111827; "
            "letter-spacing: -0.1px;"
        )
        title_label.setWordWrap(True)
        layout.addWidget(title_label)

        # Bottom row
        bottom = QHBoxLayout()
        bottom.setSpacing(12)

        time_label = QLabel(time_ago)
        time_label.setStyleSheet("font-size: 12px; color: #6B7280; font-weight: 400;")
        bottom.addWidget(time_label)

        duration_label = QLabel(duration)
        duration_label.setStyleSheet(
            "font-size: 12px; color: #6B7280; font-weight: 400;"
        )
        bottom.addWidget(duration_label)

        bottom.addStretch()

        status_label = QLabel(status)
        if status == "Transcribed":
            status_label.setStyleSheet(
                "background-color: #D1FAE5; color: #065F46; "
                "padding: 4px 12px; border-radius: 10px; font-size: 11px; font-weight: 600; "
                "border: 1px solid #A7F3D0;"
            )
        else:
            status_label.setStyleSheet(
                "background-color: #FED7AA; color: #92400E; "
                "padding: 4px 12px; border-radius: 10px; font-size: 11px; font-weight: 600; "
                "border: 1px solid #FDBA74;"
            )
        bottom.addWidget(status_label)

        layout.addLayout(bottom)

    def mousePressEvent(self, event) -> None:
        target = self.session_path or self.title
        self.clicked.emit(target)
        super().mousePressEvent(event)
