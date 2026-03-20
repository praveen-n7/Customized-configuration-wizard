"""Base Machine Information Page"""
from __future__ import annotations

try:
    from PyQt6.QtWidgets import (
        QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
        QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox,
        QGroupBox, QFrame, QSizePolicy, QPushButton, QFileDialog,
    )
    from PyQt6.QtCore import Qt
except ImportError:
    from PySide6.QtWidgets import (
        QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
        QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox,
        QGroupBox, QFrame, QSizePolicy, QPushButton, QFileDialog,
    )
    from PySide6.QtCore import Qt

from pages.base_page import BasePage
from config.machine_config import MachineConfig


class BaseMachineInfoPage(BasePage):
    PAGE_TITLE = "Base Machine Information"
    PAGE_SUBTITLE = "Configure core machine parameters, axes, and Mesa hardware"

    AXIS_CONFIGS = ["XZ", "XYZ", "XYZA", "XYZB", "XYZC", "XYZAB", "XYZABC"]
    MESA_BOARDS = [
        "5i25", "6i25", "7i76e", "7i92", "7i92T",
        "7i96", "7i96S", "5i20", "5i23", "5i24",
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 24, 32, 24)
        root.setSpacing(16)

        # ── Machine Identity ──────────────────────────────────────────────────
        id_group = QGroupBox("Machine Identity")
        id_grid = QGridLayout(id_group)
        id_grid.setColumnStretch(1, 1)
        id_grid.setHorizontalSpacing(16)
        id_grid.setVerticalSpacing(10)

        self._machine_name = QLineEdit()
        self._machine_name.setPlaceholderText("my_lathe")
        id_grid.addWidget(QLabel("Machine Name:"), 0, 0)
        id_grid.addWidget(self._machine_name, 0, 1)

        config_row = QHBoxLayout()
        self._config_dir = QLineEdit()
        self._config_dir.setPlaceholderText("/home/user/linuxcnc/configs/my_machine")
        browse_btn = QPushButton("Browse…")
        browse_btn.setFixedWidth(90)
        browse_btn.clicked.connect(self._browse_dir)
        config_row.addWidget(self._config_dir)
        config_row.addWidget(browse_btn)
        id_grid.addWidget(QLabel("Config Directory:"), 1, 0)
        id_grid.addLayout(config_row, 1, 1)

        root.addWidget(id_group)

        # ── Kinematics & Units ────────────────────────────────────────────────
        kin_group = QGroupBox("Kinematics & Units")
        kin_grid = QGridLayout(kin_group)
        kin_grid.setHorizontalSpacing(16)
        kin_grid.setVerticalSpacing(10)

        self._axis_config = QComboBox()
        self._axis_config.addItems(self.AXIS_CONFIGS)
        kin_grid.addWidget(QLabel("Axis Configuration:"), 0, 0)
        kin_grid.addWidget(self._axis_config, 0, 1)

        self._units = QComboBox()
        self._units.addItems(["Metric (mm)", "Imperial (inch)"])
        kin_grid.addWidget(QLabel("Machine Units:"), 1, 0)
        kin_grid.addWidget(self._units, 1, 1)

        root.addWidget(kin_group)

        # ── Timing ───────────────────────────────────────────────────────────
        timing_group = QGroupBox("Real-Time Timing")
        timing_grid = QGridLayout(timing_group)
        timing_grid.setHorizontalSpacing(16)
        timing_grid.setVerticalSpacing(10)

        self._servo_period = QSpinBox()
        self._servo_period.setRange(100000, 10000000)
        self._servo_period.setSingleStep(100000)
        self._servo_period.setValue(1000000)
        self._servo_period.setSuffix(" ns")
        self._servo_period.setToolTip(
            "Servo period in nanoseconds. 1000000 ns = 1 ms (1 kHz). "
            "Lower is faster but requires a faster real-time kernel."
        )
        timing_grid.addWidget(QLabel("Servo Period:"), 0, 0)
        timing_grid.addWidget(self._servo_period, 0, 1)

        self._servo_period_ms = QLabel("= 1.000 ms  (1000 Hz)")
        self._servo_period_ms.setStyleSheet("color: #A3BE8C; font-family: monospace;")
        timing_grid.addWidget(self._servo_period_ms, 0, 2)
        self._servo_period.valueChanged.connect(self._update_period_display)

        self._num_ports = QSpinBox()
        self._num_ports.setRange(1, 4)
        self._num_ports.setValue(1)
        timing_grid.addWidget(QLabel("I/O Control Ports:"), 1, 0)
        timing_grid.addWidget(self._num_ports, 1, 1)

        root.addWidget(timing_group)

        # ── Mesa Hardware ─────────────────────────────────────────────────────
        mesa_group = QGroupBox("Mesa FPGA Board")
        mesa_grid = QGridLayout(mesa_group)
        mesa_grid.setHorizontalSpacing(16)
        mesa_grid.setVerticalSpacing(10)

        self._mesa_board = QComboBox()
        self._mesa_board.addItems(self.MESA_BOARDS)
        self._mesa_board.setCurrentText("7i76e")
        mesa_grid.addWidget(QLabel("Board Model:"), 0, 0)
        mesa_grid.addWidget(self._mesa_board, 0, 1)

        board_hint = QLabel(
            "The Mesa board model determines available connectors and pin count. "
            "Select the board you have physically installed."
        )
        board_hint.setWordWrap(True)
        board_hint.setStyleSheet("color: #4C566A; font-size: 8.5pt;")
        mesa_grid.addWidget(board_hint, 1, 0, 1, 2)

        root.addWidget(mesa_group)
        root.addStretch()

    def _browse_dir(self):
        path = QFileDialog.getExistingDirectory(self, "Select Config Directory", "/home")
        if path:
            self._config_dir.setText(path)

    def _update_period_display(self, ns: int):
        ms = ns / 1_000_000
        hz = 1_000_000_000 / ns if ns > 0 else 0
        self._servo_period_ms.setText(f"= {ms:.3f} ms  ({hz:.0f} Hz)")

    def populate(self, cfg: MachineConfig):
        self._machine_name.setText(cfg.machine_name)
        self._config_dir.setText(cfg.config_directory)
        idx = self._axis_config.findText(cfg.axis_config)
        if idx >= 0:
            self._axis_config.setCurrentIndex(idx)
        self._units.setCurrentIndex(0 if cfg.units == "metric" else 1)
        self._servo_period.setValue(cfg.servo_period_ns)
        self._num_ports.setValue(cfg.num_io_ports)
        idx = self._mesa_board.findText(cfg.mesa.board_name)
        if idx >= 0:
            self._mesa_board.setCurrentIndex(idx)

    def save(self, cfg: MachineConfig):
        cfg.machine_name = self._machine_name.text().strip() or "my_machine"
        cfg.config_directory = self._config_dir.text().strip()
        cfg.axis_config = self._axis_config.currentText()
        cfg.units = "metric" if self._units.currentIndex() == 0 else "imperial"
        cfg.servo_period_ns = self._servo_period.value()
        cfg.num_io_ports = self._num_ports.value()
        cfg.mesa.board_name = self._mesa_board.currentText()
        cfg.ensure_axes()

    def validate(self):
        if not self._machine_name.text().strip():
            return False, "Machine name cannot be empty."
        if not self._config_dir.text().strip():
            return False, "Configuration directory cannot be empty."
        return True, ""
