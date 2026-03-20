"""Welcome Page"""
from __future__ import annotations

try:
    from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel,
                                  QPushButton, QFrame, QSizePolicy, QSpacerItem)
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QFont, QPixmap
except ImportError:
    from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel,
                                   QPushButton, QFrame, QSizePolicy, QSpacerItem)
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QFont, QPixmap

from pages.base_page import BasePage


class WelcomePage(BasePage):
    PAGE_TITLE = "Welcome"
    PAGE_SUBTITLE = "LinuxCNC Mesa Card Configuration Wizard"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 40, 40, 40)
        root.setSpacing(0)

        # ── Hero card ────────────────────────────────────────────────────────
        card = QFrame()
        card.setObjectName("pagePanel")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(48, 48, 48, 48)
        card_layout.setSpacing(20)

        # Logo / icon row
        icon_row = QHBoxLayout()
        icon_label = QLabel("⚙")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(52)
        icon_label.setFont(font)
        icon_label.setStyleSheet("color: #5E81AC;")
        icon_row.addStretch()
        icon_row.addWidget(icon_label)
        icon_row.addStretch()
        card_layout.addLayout(icon_row)

        # Title
        title = QLabel("PNCconf Qt Wizard")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tf = QFont()
        tf.setPointSize(22)
        tf.setWeight(QFont.Weight.Bold)
        title.setFont(tf)
        title.setStyleSheet("color: #ECEFF4;")
        card_layout.addWidget(title)

        # Subtitle
        subtitle = QLabel("LinuxCNC Mesa Card Configuration Wizard")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #81A1C1; font-size: 12pt;")
        card_layout.addWidget(subtitle)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #3A3A50;")
        card_layout.addWidget(sep)

        # Description
        desc = QLabel(
            "This wizard will guide you through configuring your LinuxCNC machine "
            "with Mesa FPGA interface cards.\n\n"
            "You can create a new configuration or modify an existing one.\n\n"
            "The wizard will generate the INI and HAL files required by LinuxCNC."
        )
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setStyleSheet("color: #A0A8B8; font-size: 10pt; line-height: 1.6;")
        card_layout.addWidget(desc)

        # Version info row
        ver_row = QHBoxLayout()
        ver_row.addStretch()
        for label, value in [("Version", "1.0.0"), ("LinuxCNC", "2.9+"), ("Mesa", "7i76/7i76e")]:
            chip = QFrame()
            chip.setStyleSheet(
                "background-color: #2A2A3C; border: 1px solid #3A3A50; "
                "border-radius: 4px; padding: 4px 10px;"
            )
            chip_layout = QHBoxLayout(chip)
            chip_layout.setContentsMargins(8, 4, 8, 4)
            lbl = QLabel(f"<b style='color:#5E81AC'>{label}:</b> "
                         f"<span style='color:#ECEFF4'>{value}</span>")
            chip_layout.addWidget(lbl)
            ver_row.addWidget(chip)
            ver_row.addSpacing(8)
        ver_row.addStretch()
        card_layout.addLayout(ver_row)

        root.addStretch(1)
        root.addWidget(card)
        root.addStretch(2)

        # Info note
        note = QLabel(
            "⚠  Back up your existing configuration before making changes."
        )
        note.setAlignment(Qt.AlignmentFlag.AlignCenter)
        note.setStyleSheet("color: #EBCB8B; font-size: 9pt; margin-top: 16px;")
        root.addWidget(note)
