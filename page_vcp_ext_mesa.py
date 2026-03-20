"""
VCP Page, External Controls Page, Mesa Config Page
"""
from __future__ import annotations

try:
    from PyQt6.QtWidgets import (
        QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit,
        QComboBox, QSpinBox, QDoubleSpinBox, QGroupBox, QCheckBox,
        QPushButton, QFileDialog, QFrame,
    )
    from PyQt6.QtCore import Qt
except ImportError:
    from PySide6.QtWidgets import (
        QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit,
        QComboBox, QSpinBox, QDoubleSpinBox, QGroupBox, QCheckBox,
        QPushButton, QFileDialog, QFrame,
    )
    from PySide6.QtCore import Qt

from pages.base_page import BasePage
from config.machine_config import MachineConfig


# ─────────────────────────────────────────────────────────────────────────────
# VCP Page
# ─────────────────────────────────────────────────────────────────────────────

class VCPPage(BasePage):
    PAGE_TITLE = "Virtual Control Panel"
    PAGE_SUBTITLE = "Configure PyVCP or GladeVCP panel embedding"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 24, 32, 24)
        root.setSpacing(16)

        # ── PyVCP ──────────────────────────────────────────────────────────
        pyvcp_group = QGroupBox("PyVCP Panel")
        pyvcp_layout = QGridLayout(pyvcp_group)
        pyvcp_layout.setVerticalSpacing(10)
        pyvcp_layout.setHorizontalSpacing(16)

        self._use_pyvcp = QCheckBox("Include PyVCP panel")
        pyvcp_layout.addWidget(self._use_pyvcp, 0, 0, 1, 2)

        self._pyvcp_file = QLineEdit()
        self._pyvcp_file.setPlaceholderText("custom_panel.xml")
        self._pyvcp_browse = QPushButton("Browse…")
        self._pyvcp_browse.setFixedWidth(90)
        self._pyvcp_browse.clicked.connect(
            lambda: self._browse_file(self._pyvcp_file, "XML Files (*.xml)")
        )
        pyvcp_layout.addWidget(QLabel("Panel XML File:"), 1, 0)
        pyvcp_layout.addWidget(self._pyvcp_file, 1, 1)
        pyvcp_layout.addWidget(self._pyvcp_browse, 1, 2)

        self._use_pyvcp.toggled.connect(self._pyvcp_file.setEnabled)
        self._use_pyvcp.toggled.connect(self._pyvcp_browse.setEnabled)
        self._pyvcp_file.setEnabled(False)
        self._pyvcp_browse.setEnabled(False)

        root.addWidget(pyvcp_group)

        # ── GladeVCP ───────────────────────────────────────────────────────
        glade_group = QGroupBox("GladeVCP Panel")
        glade_layout = QGridLayout(glade_group)
        glade_layout.setVerticalSpacing(10)
        glade_layout.setHorizontalSpacing(16)

        self._use_gladevcp = QCheckBox("Include GladeVCP panel")
        glade_layout.addWidget(self._use_gladevcp, 0, 0, 1, 2)

        self._gladevcp_file = QLineEdit()
        self._gladevcp_file.setPlaceholderText("custom_panel.glade")
        self._glade_browse = QPushButton("Browse…")
        self._glade_browse.setFixedWidth(90)
        self._glade_browse.clicked.connect(
            lambda: self._browse_file(self._gladevcp_file, "Glade Files (*.glade)")
        )
        glade_layout.addWidget(QLabel("Glade File:"), 1, 0)
        glade_layout.addWidget(self._gladevcp_file, 1, 1)
        glade_layout.addWidget(self._glade_browse, 1, 2)

        self._use_gladevcp.toggled.connect(self._gladevcp_file.setEnabled)
        self._use_gladevcp.toggled.connect(self._glade_browse.setEnabled)
        self._gladevcp_file.setEnabled(False)
        self._glade_browse.setEnabled(False)

        root.addWidget(glade_group)

        # ── Embedding ──────────────────────────────────────────────────────
        embed_group = QGroupBox("Panel Embedding")
        embed_layout = QGridLayout(embed_group)
        embed_layout.setHorizontalSpacing(16)

        self._embed = QComboBox()
        self._embed.addItems(["none", "side", "bottom", "tab"])
        embed_layout.addWidget(QLabel("Embed Location:"), 0, 0)
        embed_layout.addWidget(self._embed, 0, 1)

        root.addWidget(embed_group)
        root.addStretch()

    def _browse_file(self, target: QLineEdit, filter_str: str):
        path, _ = QFileDialog.getOpenFileName(self, "Select File", "/home", filter_str)
        if path:
            target.setText(path)

    def populate(self, cfg: MachineConfig):
        v = cfg.vcp
        self._use_pyvcp.setChecked(v.include_pyvcp)
        self._pyvcp_file.setText(v.pyvcp_file)
        self._use_gladevcp.setChecked(v.include_gladevcp)
        self._gladevcp_file.setText(v.gladevcp_file)
        idx = self._embed.findText(v.embed_panel)
        if idx >= 0: self._embed.setCurrentIndex(idx)

    def save(self, cfg: MachineConfig):
        v = cfg.vcp
        v.include_pyvcp = self._use_pyvcp.isChecked()
        v.pyvcp_file = self._pyvcp_file.text()
        v.include_gladevcp = self._use_gladevcp.isChecked()
        v.gladevcp_file = self._gladevcp_file.text()
        v.embed_panel = self._embed.currentText()


# ─────────────────────────────────────────────────────────────────────────────
# External Controls Page
# ─────────────────────────────────────────────────────────────────────────────

class ExternalControlsPage(BasePage):
    PAGE_TITLE = "External Controls"
    PAGE_SUBTITLE = "Configure external jogging, MPG, and VFD devices"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 24, 32, 24)
        root.setSpacing(16)

        # ── Serial VFD ─────────────────────────────────────────────────────
        vfd_group = QGroupBox("Serial VFD (Variable Frequency Drive)")
        vfd_layout = QVBoxLayout(vfd_group)
        self._use_vfd = QCheckBox("Enable Serial VFD")
        vfd_layout.addWidget(self._use_vfd)

        vfd_type_row = QHBoxLayout()
        self._vfd_type = QComboBox()
        self._vfd_type.addItems(["gs2", "vfs11", "hy_vfd", "abb_badvfd", "smc_gs2"])
        vfd_type_row.addWidget(QLabel("VFD Driver:"))
        vfd_type_row.addWidget(self._vfd_type)
        vfd_type_row.addStretch()
        vfd_layout.addLayout(vfd_type_row)

        self._use_vfd.toggled.connect(self._vfd_type.setEnabled)
        self._vfd_type.setEnabled(False)
        root.addWidget(vfd_group)

        # ── Jogging ────────────────────────────────────────────────────────
        jog_group = QGroupBox("Jogging")
        jog_layout = QVBoxLayout(jog_group)

        self._use_ext_jog = QCheckBox("External Button Jogging")
        self._use_mpg = QCheckBox("External MPG (Manual Pulse Generator)")
        self._use_usb_jog = QCheckBox("USB Joystick Jogging")

        for cb in [self._use_ext_jog, self._use_mpg, self._use_usb_jog]:
            jog_layout.addWidget(cb)

        mpg_row = QHBoxLayout()
        mpg_row.addSpacing(24)
        mpg_row.addWidget(QLabel("MPG Increments:"))
        self._mpg_increments = QLineEdit()
        self._mpg_increments.setPlaceholderText("0.1 0.01 0.001")
        mpg_row.addWidget(self._mpg_increments)
        jog_layout.addLayout(mpg_row)
        self._use_mpg.toggled.connect(self._mpg_increments.setEnabled)
        self._mpg_increments.setEnabled(False)

        root.addWidget(jog_group)

        # ── Override Controls ──────────────────────────────────────────────
        override_group = QGroupBox("External Override Controls")
        override_layout = QVBoxLayout(override_group)
        self._use_feed_override = QCheckBox("External Feed Override")
        self._use_max_vel = QCheckBox("External Max Velocity Override")
        self._use_spindle_override = QCheckBox("External Spindle Override")
        for cb in [self._use_feed_override, self._use_max_vel, self._use_spindle_override]:
            override_layout.addWidget(cb)

        root.addWidget(override_group)
        root.addStretch()

    def populate(self, cfg: MachineConfig):
        e = cfg.external
        self._use_vfd.setChecked(e.use_serial_vfd)
        self._vfd_type.setCurrentText(cfg.spindle.vfd_type)
        self._use_ext_jog.setChecked(e.use_ext_jogging)
        self._use_mpg.setChecked(e.use_mpg)
        self._mpg_increments.setText(e.mpg_increments)
        self._use_usb_jog.setChecked(e.use_usb_jogging)
        self._use_feed_override.setChecked(e.use_feed_override)
        self._use_max_vel.setChecked(e.use_max_vel_override)
        self._use_spindle_override.setChecked(e.use_spindle_override)

    def save(self, cfg: MachineConfig):
        e = cfg.external
        e.use_serial_vfd = self._use_vfd.isChecked()
        cfg.spindle.vfd_type = self._vfd_type.currentText() if e.use_serial_vfd else "none"
        e.use_ext_jogging = self._use_ext_jog.isChecked()
        e.use_mpg = self._use_mpg.isChecked()
        e.mpg_increments = self._mpg_increments.text() or "0.1 0.01 0.001"
        e.use_usb_jogging = self._use_usb_jog.isChecked()
        e.use_feed_override = self._use_feed_override.isChecked()
        e.use_max_vel_override = self._use_max_vel.isChecked()
        e.use_spindle_override = self._use_spindle_override.isChecked()


# ─────────────────────────────────────────────────────────────────────────────
# Mesa Card Configuration Page
# ─────────────────────────────────────────────────────────────────────────────

class MesaConfigPage(BasePage):
    PAGE_TITLE = "Mesa Card Configuration"
    PAGE_SUBTITLE = "Configure Mesa FPGA board firmware and signal parameters"

    FIRMWARES = {
        "5i25": ["5i25_prob_rf.bit", "5i25_sserial.bit", "5i25_t7i76d.bit"],
        "7i76e": ["7i76e.bit", "7i76e_7i76.bit"],
        "7i92": ["7i92_5abcg20.bit", "7i92_7i76x2.bit"],
        "7i96": ["7i96.bit", "7i96_s.bit"],
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 24, 32, 24)
        root.setSpacing(16)

        # ── Board & Firmware ───────────────────────────────────────────────
        hw_group = QGroupBox("Board & Firmware")
        hw_grid = QGridLayout(hw_group)
        hw_grid.setHorizontalSpacing(16)
        hw_grid.setVerticalSpacing(10)

        self._board = QComboBox()
        self._board.addItems(["5i25", "6i25", "7i76e", "7i92", "7i96", "7i96S"])
        self._board.currentTextChanged.connect(self._update_firmware_list)
        hw_grid.addWidget(QLabel("Board Name:"), 0, 0)
        hw_grid.addWidget(self._board, 0, 1)

        self._firmware = QComboBox()
        self._firmware.setEditable(True)
        hw_grid.addWidget(QLabel("Firmware:"), 1, 0)
        hw_grid.addWidget(self._firmware, 1, 1)

        root.addWidget(hw_group)

        # ── Signal Frequencies ─────────────────────────────────────────────
        freq_group = QGroupBox("Signal Frequencies")
        freq_grid = QGridLayout(freq_group)
        freq_grid.setHorizontalSpacing(16)
        freq_grid.setVerticalSpacing(10)

        self._pwm_freq = QSpinBox()
        self._pwm_freq.setRange(1000, 1000000)
        self._pwm_freq.setValue(100000)
        self._pwm_freq.setSuffix(" Hz")
        freq_grid.addWidget(QLabel("PWM Base Frequency:"), 0, 0)
        freq_grid.addWidget(self._pwm_freq, 0, 1)

        self._pdm_freq = QSpinBox()
        self._pdm_freq.setRange(1000000, 100000000)
        self._pdm_freq.setSingleStep(1000000)
        self._pdm_freq.setValue(6000000)
        self._pdm_freq.setSuffix(" Hz")
        freq_grid.addWidget(QLabel("PDM Base Frequency:"), 1, 0)
        freq_grid.addWidget(self._pdm_freq, 1, 1)

        self._watchdog = QDoubleSpinBox()
        self._watchdog.setRange(1.0, 1000.0)
        self._watchdog.setValue(10.0)
        self._watchdog.setSuffix(" ms")
        self._watchdog.setDecimals(1)
        freq_grid.addWidget(QLabel("Watchdog Timeout:"), 2, 0)
        freq_grid.addWidget(self._watchdog, 2, 1)

        root.addWidget(freq_group)

        # ── Channel Counts ─────────────────────────────────────────────────
        ch_group = QGroupBox("Channel Counts")
        ch_grid = QGridLayout(ch_group)
        ch_grid.setHorizontalSpacing(16)
        ch_grid.setVerticalSpacing(10)

        self._encoders = QSpinBox()
        self._encoders.setRange(0, 32)
        self._encoders.setValue(1)
        ch_grid.addWidget(QLabel("Encoders:"), 0, 0)
        ch_grid.addWidget(self._encoders, 0, 1)

        self._stepgens = QSpinBox()
        self._stepgens.setRange(0, 32)
        self._stepgens.setValue(5)
        ch_grid.addWidget(QLabel("Step Generators:"), 1, 0)
        ch_grid.addWidget(self._stepgens, 1, 1)

        self._smart_serial = QSpinBox()
        self._smart_serial.setRange(0, 8)
        self._smart_serial.setValue(0)
        ch_grid.addWidget(QLabel("Smart Serial Ports:"), 2, 0)
        ch_grid.addWidget(self._smart_serial, 2, 1)

        root.addWidget(ch_group)
        root.addStretch()

        self._update_firmware_list(self._board.currentText())

    def _update_firmware_list(self, board: str):
        self._firmware.clear()
        fw_list = self.FIRMWARES.get(board, [f"{board}.bit"])
        self._firmware.addItems(fw_list)

    def populate(self, cfg: MachineConfig):
        m = cfg.mesa
        self._board.setCurrentText(m.board_name)
        self._update_firmware_list(m.board_name)
        self._firmware.setCurrentText(m.firmware)
        self._pwm_freq.setValue(m.pwm_base_freq)
        self._pdm_freq.setValue(m.pdm_base_freq)
        self._watchdog.setValue(m.watchdog_timeout)
        self._encoders.setValue(m.num_encoders)
        self._stepgens.setValue(m.num_stepgens)
        self._smart_serial.setValue(m.num_smart_serial)

    def save(self, cfg: MachineConfig):
        m = cfg.mesa
        m.board_name = self._board.currentText()
        m.firmware = self._firmware.currentText()
        m.pwm_base_freq = self._pwm_freq.value()
        m.pdm_base_freq = self._pdm_freq.value()
        m.watchdog_timeout = self._watchdog.value()
        m.num_encoders = self._encoders.value()
        m.num_stepgens = self._stepgens.value()
        m.num_smart_serial = self._smart_serial.value()
