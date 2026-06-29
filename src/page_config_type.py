"""Configuration Type Page"""
from __future__ import annotations

try:
    from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel,
                                  QRadioButton, QFrame, QButtonGroup,
                                  QPushButton, QLineEdit, QFileDialog)
    from PyQt6.QtCore import Qt
except ImportError:
    from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel,
                                   QRadioButton, QFrame, QButtonGroup,
                                   QPushButton, QLineEdit, QFileDialog)
    from PySide6.QtCore import Qt

from pages.base_page import BasePage
from config.machine_config import MachineConfig


class ConfigTypePage(BasePage):
    PAGE_TITLE = "Configuration Type"
    PAGE_SUBTITLE = "Create a new configuration or modify an existing one"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 32, 40, 32)
        root.setSpacing(20)

        # ── Choice cards ──────────────────────────────────────────────────────
        choice_row = QHBoxLayout()
        choice_row.setSpacing(16)

        self._btn_new = self._make_choice_card(
            "＋  Create New Configuration",
            "Start fresh with a new LinuxCNC configuration.",
            True,
        )
        self._btn_modify = self._make_choice_card(
            "✎  Modify Existing Configuration",
            "Open and edit an existing configuration directory.",
            False,
        )
        choice_row.addWidget(self._btn_new_frame)
        choice_row.addWidget(self._btn_modify_frame)
        root.addLayout(choice_row)

        # ── Existing config path (shown only when Modify selected) ────────────
        self._existing_frame = QFrame()
        self._existing_frame.setObjectName("pagePanel")
        exist_layout = QVBoxLayout(self._existing_frame)
        exist_layout.setContentsMargins(20, 16, 20, 16)

        lbl = QLabel("Existing Configuration Path:")
        lbl.setStyleSheet("color: #81A1C1; font-weight: 600;")
        exist_layout.addWidget(lbl)

        path_row = QHBoxLayout()
        self._existing_path = QLineEdit()
        self._existing_path.setPlaceholderText("/home/user/linuxcnc/configs/my_machine")
        self._browse_btn = QPushButton("Browse…")
        self._browse_btn.setFixedWidth(90)
        self._browse_btn.clicked.connect(self._browse_existing)
        path_row.addWidget(self._existing_path)
        path_row.addWidget(self._browse_btn)
        exist_layout.addLayout(path_row)

        hint = QLabel("Select the directory containing your existing .ini file.")
        hint.setProperty("class", "hint")
        hint.setStyleSheet("color: #4C566A; font-size: 8.5pt;")
        exist_layout.addWidget(hint)

        self._existing_frame.setVisible(False)
        root.addWidget(self._existing_frame)
        root.addStretch()

        # Connect radios
        self._btn_new.toggled.connect(
            lambda checked: self._existing_frame.setVisible(not checked)
        )

    def _make_choice_card(self, title: str, desc: str, checked: bool):
        frame = QFrame()
        frame.setObjectName("pagePanel")
        frame.setStyleSheet(
            "QFrame#pagePanel { border: 2px solid #3A3A50; border-radius: 8px; }"
            "QFrame#pagePanel:hover { border-color: #5E81AC; }"
        )
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(10)

        radio = QRadioButton(title)
        radio.setChecked(checked)
        radio.setStyleSheet("font-size: 11pt; font-weight: 600;")
        layout.addWidget(radio)

        desc_lbl = QLabel(desc)
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet("color: #81A1C1; font-size: 9.5pt; padding-left: 24px;")
        layout.addWidget(desc_lbl)

        # Store references
        if checked:
            self._btn_new = radio
            self._btn_new_frame = frame
        else:
            self._btn_modify = radio
            self._btn_modify_frame = frame

        return radio

    def _browse_existing(self):
        path = QFileDialog.getExistingDirectory(
            self, "Select Configuration Directory",
            "/home"
        )
        if path:
            self._existing_path.setText(path)

    def populate(self, cfg: MachineConfig):
        if cfg.config_type == "modify":
            self._btn_modify.setChecked(True)
        else:
            self._btn_new.setChecked(True)

    def save(self, cfg: MachineConfig):
        cfg.config_type = "modify" if self._btn_modify.isChecked() else "new"
        if cfg.config_type == "modify":
            cfg.config_directory = self._existing_path.text()
