"""
VCP Page, External Controls Page, Mesa Config Page
Full Feature Parity with original LinuxCNC GTK PnCConf wizard.
"""
from __future__ import annotations

try:
    from PyQt6.QtWidgets import (
        QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit,
        QComboBox, QSpinBox, QDoubleSpinBox, QGroupBox, QCheckBox,
        QPushButton, QFileDialog, QFrame, QScrollArea, QWidget,
        QTabWidget, QRadioButton, QButtonGroup,
        QTableWidget, QTableWidgetItem, QHeaderView,
    )
    from PyQt6.QtCore import Qt
except ImportError:
    from PySide6.QtWidgets import (
        QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit,
        QComboBox, QSpinBox, QDoubleSpinBox, QGroupBox, QCheckBox,
        QPushButton, QFileDialog, QFrame, QScrollArea, QWidget,
        QTabWidget, QRadioButton, QButtonGroup,
        QTableWidget, QTableWidgetItem, QHeaderView,
    )
    from PySide6.QtCore import Qt

from pages.base_page import BasePage
from config.machine_config import MachineConfig

_HINT = "color: #4C566A; font-size: 8.5pt;"


# ─────────────────────────────────────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────────────────────────────────────

def _scroll_page(inner_widget: QWidget) -> QScrollArea:
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.Shape.NoFrame)
    scroll.setWidget(inner_widget)
    return scroll


# ─────────────────────────────────────────────────────────────────────────────
# VCP PAGE
# ─────────────────────────────────────────────────────────────────────────────

class VCPPage(BasePage):
    PAGE_TITLE    = "Virtual Control Panel"
    PAGE_SUBTITLE = "Configure PyVCP or GladeVCP panel embedding and sample options"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        inner = QWidget()
        root = QVBoxLayout(inner)
        root.setContentsMargins(32, 24, 32, 24)
        root.setSpacing(16)

        root.addWidget(self._build_pyvcp_group())
        root.addWidget(self._build_gladevcp_group())
        root.addWidget(self._build_display_options_group())
        root.addWidget(self._build_embedding_group())
        root.addStretch()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(_scroll_page(inner))

    # ── PyVCP ─────────────────────────────────────────────────────────────────
    def _build_pyvcp_group(self) -> QGroupBox:
        grp = QGroupBox("PyVCP Panel")
        root = QVBoxLayout(grp)
        root.setSpacing(8)

        self._use_pyvcp = QCheckBox("Include PyVCP panel")
        root.addWidget(self._use_pyvcp)

        # File or sample selector row
        file_row = QHBoxLayout()
        self._pyvcp_file = QLineEdit()
        self._pyvcp_file.setPlaceholderText("custom_panel.xml  (leave blank to use sample)")
        self._pyvcp_browse = QPushButton("Browse…")
        self._pyvcp_browse.setFixedWidth(90)
        self._pyvcp_browse.clicked.connect(
            lambda: self._browse_file(self._pyvcp_file, "XML Files (*.xml)")
        )
        file_row.addWidget(QLabel("Panel XML File:"))
        file_row.addWidget(self._pyvcp_file)
        file_row.addWidget(self._pyvcp_browse)
        root.addLayout(file_row)

        # Sample display options
        sample_box = QGroupBox("Sample Display Options")
        sample_grid = QGridLayout(sample_box)
        sample_grid.setHorizontalSpacing(24)
        sample_grid.setVerticalSpacing(6)

        self._pyvcp_spindle_speed    = QCheckBox("Spindle Speed Indicator")
        self._pyvcp_spindle_at_speed = QCheckBox("Spindle At Speed LED")
        self._pyvcp_zero_x           = QCheckBox("Zero X button")
        self._pyvcp_zero_y           = QCheckBox("Zero Y button")
        self._pyvcp_zero_z           = QCheckBox("Zero Z button")
        self._pyvcp_zero_a           = QCheckBox("Zero A button")

        sample_grid.addWidget(self._pyvcp_spindle_speed,    0, 0)
        sample_grid.addWidget(self._pyvcp_spindle_at_speed, 0, 1)
        sample_grid.addWidget(self._pyvcp_zero_x,           1, 0)
        sample_grid.addWidget(self._pyvcp_zero_y,           1, 1)
        sample_grid.addWidget(self._pyvcp_zero_z,           2, 0)
        sample_grid.addWidget(self._pyvcp_zero_a,           2, 1)

        root.addWidget(sample_box)

        # Wire enable/disable
        def _toggle_pyvcp(enabled: bool):
            for w in [self._pyvcp_file, self._pyvcp_browse, sample_box]:
                w.setEnabled(enabled)

        self._use_pyvcp.toggled.connect(_toggle_pyvcp)
        _toggle_pyvcp(False)

        return grp

    # ── GladeVCP ──────────────────────────────────────────────────────────────
    def _build_gladevcp_group(self) -> QGroupBox:
        grp = QGroupBox("GladeVCP Panel")
        root = QVBoxLayout(grp)
        root.setSpacing(8)

        self._use_gladevcp = QCheckBox("Include GladeVCP panel")
        root.addWidget(self._use_gladevcp)

        file_row = QHBoxLayout()
        self._gladevcp_file = QLineEdit()
        self._gladevcp_file.setPlaceholderText("custom_panel.glade  (leave blank to use sample)")
        self._glade_browse = QPushButton("Browse…")
        self._glade_browse.setFixedWidth(90)
        self._glade_browse.clicked.connect(
            lambda: self._browse_file(self._gladevcp_file, "Glade Files (*.glade)")
        )
        file_row.addWidget(QLabel("Glade File:"))
        file_row.addWidget(self._gladevcp_file)
        file_row.addWidget(self._glade_browse)
        root.addLayout(file_row)

        sample_box = QGroupBox("Sample Display Options")
        sample_grid = QGridLayout(sample_box)
        sample_grid.setHorizontalSpacing(24)
        sample_grid.setVerticalSpacing(6)

        self._glade_spindle_speed    = QCheckBox("Spindle Speed Indicator")
        self._glade_spindle_at_speed = QCheckBox("Spindle At Speed LED")
        self._glade_zero_x           = QCheckBox("Zero X button")
        self._glade_zero_y           = QCheckBox("Zero Y button")
        self._glade_zero_z           = QCheckBox("Zero Z button")
        self._glade_zero_a           = QCheckBox("Zero A button")

        sample_grid.addWidget(self._glade_spindle_speed,    0, 0)
        sample_grid.addWidget(self._glade_spindle_at_speed, 0, 1)
        sample_grid.addWidget(self._glade_zero_x,           1, 0)
        sample_grid.addWidget(self._glade_zero_y,           1, 1)
        sample_grid.addWidget(self._glade_zero_z,           2, 0)
        sample_grid.addWidget(self._glade_zero_a,           2, 1)

        root.addWidget(sample_box)

        def _toggle_glade(enabled: bool):
            for w in [self._gladevcp_file, self._glade_browse, sample_box]:
                w.setEnabled(enabled)

        self._use_gladevcp.toggled.connect(_toggle_glade)
        _toggle_glade(False)

        return grp

    # ── Display / Size Options ────────────────────────────────────────────────
    def _build_display_options_group(self) -> QGroupBox:
        grp = QGroupBox("Display Options")
        g = QGridLayout(grp)
        g.setHorizontalSpacing(16)
        g.setVerticalSpacing(10)

        def ispin(lo, hi, val):
            s = QSpinBox()
            s.setRange(lo, hi)
            s.setValue(val)
            return s

        self._panel_w = ispin(50, 3840, 200)
        self._panel_h = ispin(50, 2160, 400)
        self._panel_x = ispin(0,  7680,   0)
        self._panel_y = ispin(0,  4320,   0)

        g.addWidget(QLabel("Width:"),  0, 0); g.addWidget(self._panel_w, 0, 1)
        g.addWidget(QLabel("Height:"), 0, 2); g.addWidget(self._panel_h, 0, 3)
        g.addWidget(QLabel("X Pos:"),  1, 0); g.addWidget(self._panel_x, 1, 1)
        g.addWidget(QLabel("Y Pos:"),  1, 2); g.addWidget(self._panel_y, 1, 3)

        self._panel_maximize = QCheckBox("Force maximize panel")
        g.addWidget(self._panel_maximize, 2, 0, 1, 4)

        self._follow_theme = QCheckBox("Follow system GTK theme")
        self._follow_theme.setChecked(True)
        g.addWidget(self._follow_theme, 3, 0, 1, 4)

        return grp

    # ── Embedding ─────────────────────────────────────────────────────────────
    def _build_embedding_group(self) -> QGroupBox:
        grp = QGroupBox("Embedding Options")
        root = QVBoxLayout(grp)
        self._embed_group = QButtonGroup(grp)

        options = [
            ("none",        "None (not embedded)"),
            ("center_tab",  "Center tab embedded"),
            ("right_side",  "Right-side embedded"),
            ("standalone",  "Standalone panel (separate window)"),
        ]
        self._embed_radios: dict[str, QRadioButton] = {}
        for key, label in options:
            rb = QRadioButton(label)
            self._embed_radios[key] = rb
            self._embed_group.addButton(rb)
            root.addWidget(rb)

        self._embed_radios["none"].setChecked(True)
        return grp

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _browse_file(self, target: QLineEdit, filter_str: str):
        path, _ = QFileDialog.getOpenFileName(self, "Select File", "/home", filter_str)
        if path:
            target.setText(path)

    # ── populate / save ───────────────────────────────────────────────────────
    def populate(self, cfg: MachineConfig):
        v = cfg.vcp
        self._use_pyvcp.setChecked(v.include_pyvcp)
        self._pyvcp_file.setText(v.pyvcp_file)
        self._pyvcp_spindle_speed.setChecked(v.pyvcp_spindle_speed)
        self._pyvcp_spindle_at_speed.setChecked(v.pyvcp_spindle_at_speed)
        self._pyvcp_zero_x.setChecked(v.pyvcp_zero_x)
        self._pyvcp_zero_y.setChecked(v.pyvcp_zero_y)
        self._pyvcp_zero_z.setChecked(v.pyvcp_zero_z)
        self._pyvcp_zero_a.setChecked(v.pyvcp_zero_a)

        self._use_gladevcp.setChecked(v.include_gladevcp)
        self._gladevcp_file.setText(v.gladevcp_file)
        self._glade_spindle_speed.setChecked(v.gladevcp_spindle_speed)
        self._glade_spindle_at_speed.setChecked(v.gladevcp_spindle_at_speed)
        self._glade_zero_x.setChecked(v.gladevcp_zero_x)
        self._glade_zero_y.setChecked(v.gladevcp_zero_y)
        self._glade_zero_z.setChecked(v.gladevcp_zero_z)
        self._glade_zero_a.setChecked(v.gladevcp_zero_a)

        self._panel_w.setValue(v.panel_width)
        self._panel_h.setValue(v.panel_height)
        self._panel_x.setValue(v.panel_x)
        self._panel_y.setValue(v.panel_y)
        self._panel_maximize.setChecked(v.panel_force_maximize)
        self._follow_theme.setChecked(v.follow_system_theme)

        rb = self._embed_radios.get(v.embed_panel)
        if rb:
            rb.setChecked(True)

    def save(self, cfg: MachineConfig):
        v = cfg.vcp
        v.include_pyvcp            = self._use_pyvcp.isChecked()
        v.pyvcp_file               = self._pyvcp_file.text()
        v.pyvcp_spindle_speed      = self._pyvcp_spindle_speed.isChecked()
        v.pyvcp_spindle_at_speed   = self._pyvcp_spindle_at_speed.isChecked()
        v.pyvcp_zero_x             = self._pyvcp_zero_x.isChecked()
        v.pyvcp_zero_y             = self._pyvcp_zero_y.isChecked()
        v.pyvcp_zero_z             = self._pyvcp_zero_z.isChecked()
        v.pyvcp_zero_a             = self._pyvcp_zero_a.isChecked()

        v.include_gladevcp         = self._use_gladevcp.isChecked()
        v.gladevcp_file            = self._gladevcp_file.text()
        v.gladevcp_spindle_speed   = self._glade_spindle_speed.isChecked()
        v.gladevcp_spindle_at_speed = self._glade_spindle_at_speed.isChecked()
        v.gladevcp_zero_x          = self._glade_zero_x.isChecked()
        v.gladevcp_zero_y          = self._glade_zero_y.isChecked()
        v.gladevcp_zero_z          = self._glade_zero_z.isChecked()
        v.gladevcp_zero_a          = self._glade_zero_a.isChecked()

        v.panel_width         = self._panel_w.value()
        v.panel_height        = self._panel_h.value()
        v.panel_x             = self._panel_x.value()
        v.panel_y             = self._panel_y.value()
        v.panel_force_maximize = self._panel_maximize.isChecked()
        v.follow_system_theme  = self._follow_theme.isChecked()

        for key, rb in self._embed_radios.items():
            if rb.isChecked():
                v.embed_panel = key
                break


# NOTE: ExternalControlsPage lives in page_external_controls.py (full implementation).
# The stub that was here has been removed. Do NOT re-add it here.

# ─────────────────────────────────────────────────────────────────────────────
# MESA CARD CONFIGURATION PAGE
# ─────────────────────────────────────────────────────────────────────────────

class MesaConfigPage(BasePage):
    """
    Mesa Card Configuration — Full Feature Parity with original PnCConf.

    Sections:
      Board Firmware     — board name + firmware file (dynamic, DB-driven)
      Signal Frequencies — PWM base, PDM base, Watchdog timeout
      Channel Counts     — Encoders, StepGens, PWMGens, Smart Serial
                           All clamped to firmware limits on change
      Smart Serial       — number of channels + device allocation table
      Sanity Checks      — 7i29 / 7i30 / 7i33 / 7i40 / 7i48 daughter boards
      Firmware Info      — read-only description of selected firmware
    """

    PAGE_TITLE    = "FPGA Configuration"
    PAGE_SUBTITLE = "Configure Mesa FPGA board firmware and signal parameters"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    # ─────────────────────────────────────────────────────────────────────────
    # UI construction
    # ─────────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        from config.machine_config import get_all_boards, get_firmware_list

        inner = QWidget()
        root = QVBoxLayout(inner)
        root.setContentsMargins(32, 24, 32, 24)
        root.setSpacing(16)

        # ── Board & Firmware ─────────────────────────────────────────────────
        fw_grp = QGroupBox("Board Firmware")
        fw_grid = QGridLayout(fw_grp)
        fw_grid.setHorizontalSpacing(16)
        fw_grid.setVerticalSpacing(10)

        self._board = QComboBox()
        self._board.addItems(get_all_boards())
        fw_grid.addWidget(QLabel("Board Name:"), 0, 0)
        fw_grid.addWidget(self._board, 0, 1)

        self._firmware = QComboBox()
        self._firmware.setEditable(True)
        fw_grid.addWidget(QLabel("Firmware:"), 1, 0)
        fw_grid.addWidget(self._firmware, 1, 1)

        self._fw_desc = QLabel("")
        self._fw_desc.setStyleSheet("color: #81A1C1; font-size: 8.5pt; font-style: italic;")
        self._fw_desc.setWordWrap(True)
        fw_grid.addWidget(self._fw_desc, 2, 0, 1, 2)

        # Card Address (IP for Ethernet boards, PCIe slot for PCI)
        self._card_addr = QLineEdit("192.168.1.121")
        self._card_addr.setPlaceholderText("e.g. 192.168.1.121  (Ethernet) or  0  (PCI)")
        self._card_addr.setToolTip(
            "For Ethernet boards: the IP address of the Mesa card.\n"
            "For PCI boards: the PCI slot index (usually 0).")
        fw_grid.addWidget(QLabel("Card Address:"), 3, 0)
        fw_grid.addWidget(self._card_addr, 3, 1)

        self._board.currentTextChanged.connect(self._on_board_changed)
        self._firmware.currentTextChanged.connect(self._on_firmware_changed)
        self._board.currentTextChanged.connect(self._on_board_type_changed)

        root.addWidget(fw_grp)

        # ── Signal Frequencies ───────────────────────────────────────────────
        freq_grp = QGroupBox("Signal Frequencies")
        freq_grid = QGridLayout(freq_grp)
        freq_grid.setHorizontalSpacing(16)
        freq_grid.setVerticalSpacing(10)

        self._pwm_freq = QSpinBox()
        self._pwm_freq.setRange(1_000, 1_000_000)
        self._pwm_freq.setSingleStep(1000)
        self._pwm_freq.setValue(100_000)
        self._pwm_freq.setSuffix(" Hz")
        self._pwm_freq.setToolTip(
            "PWM carrier frequency used by hm2 pwmgen instances.\n"
            "Higher = smoother but more CPU load. Typical: 20 kHz–100 kHz."
        )
        freq_grid.addWidget(QLabel("PWM Base Frequency:"), 0, 0)
        freq_grid.addWidget(self._pwm_freq, 0, 1)

        self._pdm_freq = QSpinBox()
        self._pdm_freq.setRange(1_000_000, 100_000_000)
        self._pdm_freq.setSingleStep(1_000_000)
        self._pdm_freq.setValue(6_000_000)
        self._pdm_freq.setSuffix(" Hz")
        self._pdm_freq.setToolTip(
            "PDM (Pulse Density Modulation) base frequency.\n"
            "Used when pwmgen mode is set to PDM. Typical: 6 MHz."
        )
        freq_grid.addWidget(QLabel("PDM Base Frequency:"), 1, 0)
        freq_grid.addWidget(self._pdm_freq, 1, 1)

        self._watchdog = QDoubleSpinBox()
        self._watchdog.setRange(1.0, 5000.0)
        self._watchdog.setValue(10.0)
        self._watchdog.setSuffix(" ms")
        self._watchdog.setDecimals(1)
        self._watchdog.setToolTip(
            "FPGA hardware watchdog timeout.\n"
            "If the host PC does not service the card within this window, "
            "outputs are forced safe. Must be > servo period × 1.5."
        )
        freq_grid.addWidget(QLabel("Watchdog Timeout:"), 2, 0)
        freq_grid.addWidget(self._watchdog, 2, 1)

        root.addWidget(freq_grp)

        # ── Channel Counts ───────────────────────────────────────────────────
        ch_grp = QGroupBox("Channel Counts")
        ch_grid = QGridLayout(ch_grp)
        ch_grid.setHorizontalSpacing(24)
        ch_grid.setVerticalSpacing(10)

        def _spin(lo, hi, val, tip=""):
            s = QSpinBox()
            s.setRange(lo, hi)
            s.setValue(val)
            if tip:
                s.setToolTip(tip)
            return s

        self._encoders   = _spin(0, 32, 1, "Quadrature encoder count allocated in firmware.")
        self._stepgens   = _spin(0, 32, 5, "Step/dir generator count allocated in firmware.")
        self._pwmgens    = _spin(0, 16, 0, "PWM generator count allocated in firmware.")
        self._sserial_n  = _spin(0,  8, 0, "Smart Serial port count.")
        self._ss_chans   = _spin(1,  8, 2, "Smart Serial channels per port.")

        self._enc_limit_lbl  = QLabel("")
        self._sg_limit_lbl   = QLabel("")
        self._pwm_limit_lbl  = QLabel("")
        self._ss_limit_lbl   = QLabel("")
        for lbl in [self._enc_limit_lbl, self._sg_limit_lbl,
                    self._pwm_limit_lbl, self._ss_limit_lbl]:
            lbl.setStyleSheet("color: #4C566A; font-size: 8pt;")

        ch_grid.addWidget(QLabel("Encoders:"),           0, 0)
        ch_grid.addWidget(self._encoders,                0, 1)
        ch_grid.addWidget(self._enc_limit_lbl,           0, 2)

        ch_grid.addWidget(QLabel("Step Generators:"),    1, 0)
        ch_grid.addWidget(self._stepgens,                1, 1)
        ch_grid.addWidget(self._sg_limit_lbl,            1, 2)

        ch_grid.addWidget(QLabel("PWM Generators:"),     2, 0)
        ch_grid.addWidget(self._pwmgens,                 2, 1)
        ch_grid.addWidget(self._pwm_limit_lbl,           2, 2)

        ch_grid.addWidget(QLabel("Smart Serial Ports:"), 3, 0)
        ch_grid.addWidget(self._sserial_n,               3, 1)
        ch_grid.addWidget(self._ss_limit_lbl,            3, 2)

        ch_grid.addWidget(QLabel("SS Channels/Port:"),   4, 0)
        ch_grid.addWidget(self._ss_chans,                4, 1)

        root.addWidget(ch_grp)

        # ── Smart Serial Device Allocation ───────────────────────────────────
        self._ss_grp = QGroupBox("Smart Serial Device Allocation")
        ss_layout = QVBoxLayout(self._ss_grp)

        ss_top = QHBoxLayout()
        ss_top.addWidget(QLabel("Channels:"))
        ss_top.addWidget(self._ss_chans)
        ss_top.addStretch()
        ss_layout.addLayout(ss_top)

        self._ss_table = QTableWidget(0, 3)
        self._ss_table.setHorizontalHeaderLabels(["Channel", "Device Type", "Address"])
        hdr = self._ss_table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self._ss_table.setColumnWidth(0, 70)
        self._ss_table.setColumnWidth(2, 70)
        self._ss_table.verticalHeader().setVisible(False)
        self._ss_table.setMaximumHeight(160)
        ss_layout.addWidget(self._ss_table)
        self._ss_grp.setVisible(False)

        self._sserial_n.valueChanged.connect(self._on_sserial_count_changed)
        self._ss_chans.valueChanged.connect(self._rebuild_ss_table)

        root.addWidget(self._ss_grp)

        # ── Sanity Checks ────────────────────────────────────────────────────
        san_grp = QGroupBox("Sanity Checks")
        san_grid = QGridLayout(san_grp)
        san_grid.setHorizontalSpacing(24)
        san_grid.setVerticalSpacing(6)
        hint = QLabel(
            "Click on each page tab to configure signal names for each connector port.\n"
            "Tabbed pages accept the changes. Figure signal names for each connector port."
        )
        hint.setStyleSheet("color: #4C566A; font-size: 8.5pt;")
        hint.setWordWrap(True)
        san_grid.addWidget(hint, 0, 0, 1, 2)

        self._cb_7i29 = QCheckBox("7i29 daughter board")
        self._cb_7i30 = QCheckBox("7i30 daughter board")
        self._cb_7i33 = QCheckBox("7i33 daughter board")
        self._cb_7i40 = QCheckBox("7i40 daughter board")
        self._cb_7i48 = QCheckBox("7i48 daughter board")

        san_grid.addWidget(self._cb_7i29, 1, 0)
        san_grid.addWidget(self._cb_7i30, 1, 1)
        san_grid.addWidget(self._cb_7i33, 2, 0)
        san_grid.addWidget(self._cb_7i40, 2, 1)
        san_grid.addWidget(self._cb_7i48, 3, 0)

        root.addWidget(san_grp)
        root.addStretch()

        # Wrap in scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(inner)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        # Init
        self._on_board_changed(self._board.currentText())

    # ─────────────────────────────────────────────────────────────────────────
    # Dynamic update slots
    # ─────────────────────────────────────────────────────────────────────────

    def _on_board_type_changed(self, board: str):
        """Update card address placeholder based on board type."""
        eth_boards = {"7i76e", "7i92", "7i96", "7i96S"}
        if board in eth_boards:
            self._card_addr.setPlaceholderText("e.g. 192.168.1.121  (Ethernet)")
        else:
            self._card_addr.setPlaceholderText("PCI slot index, e.g.  0")

    def _on_board_changed(self, board: str):
        from config.machine_config import get_firmware_list
        self._firmware.blockSignals(True)
        self._firmware.clear()
        self._firmware.addItems(get_firmware_list(board) or [f"{board}.bit"])
        self._firmware.blockSignals(False)
        self._on_firmware_changed(self._firmware.currentText())

    def _on_firmware_changed(self, fw: str):
        from config.machine_config import get_firmware_spec
        board = self._board.currentText()
        spec = get_firmware_spec(board, fw)
        if spec:
            self._fw_desc.setText(f"ℹ  {spec.description}")
            self._enc_limit_lbl.setText(f"max {spec.max_encoders}")
            self._sg_limit_lbl.setText(f"max {spec.max_stepgens}")
            self._pwm_limit_lbl.setText(f"max {spec.max_pwmgens}")
            self._ss_limit_lbl.setText(f"max {spec.max_sserials}")
            # Clamp spinboxes silently
            self._encoders.setMaximum(spec.max_encoders)
            self._stepgens.setMaximum(spec.max_stepgens)
            self._pwmgens.setMaximum(spec.max_pwmgens)
            self._sserial_n.setMaximum(spec.max_sserials)
        else:
            self._fw_desc.setText("(custom firmware — limits unknown)")
            for lbl in [self._enc_limit_lbl, self._sg_limit_lbl,
                        self._pwm_limit_lbl, self._ss_limit_lbl]:
                lbl.setText("")

    def _on_sserial_count_changed(self, n: int):
        self._ss_grp.setVisible(n > 0)
        if n > 0:
            self._rebuild_ss_table()

    def _rebuild_ss_table(self):
        """Rebuild smart serial allocation table."""
        n_ports = self._sserial_n.value()
        n_chans = self._ss_chans.value()
        total   = n_ports * n_chans
        self._ss_table.setRowCount(total)
        row = 0
        for port in range(n_ports):
            for ch in range(n_chans):
                ch_item = QTableWidgetItem(f"Port {port}, Ch {ch}")
                ch_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                self._ss_table.setItem(row, 0, ch_item)

                dev_combo = QComboBox()
                dev_combo.addItems(["Unused", "7i76", "7i77", "7i64", "7i84"])
                self._ss_table.setCellWidget(row, 1, dev_combo)

                addr_spin = QSpinBox()
                addr_spin.setRange(0, 15)
                self._ss_table.setCellWidget(row, 2, addr_spin)
                row += 1

    # ─────────────────────────────────────────────────────────────────────────
    # populate / save
    # ─────────────────────────────────────────────────────────────────────────

    def populate(self, cfg: MachineConfig):
        m = cfg.mesa

        self._board.blockSignals(True)
        self._board.setCurrentText(m.board_name)
        self._board.blockSignals(False)

        self._on_board_changed(m.board_name)
        self._on_board_type_changed(m.board_name)

        self._firmware.setCurrentText(m.firmware)
        self._card_addr.setText(getattr(m, "ip_address", "192.168.1.121"))
        self._pwm_freq.setValue(m.pwm_base_freq)
        self._pdm_freq.setValue(m.pdm_base_freq)
        self._watchdog.setValue(m.watchdog_timeout)
        self._encoders.setValue(m.num_encoders)
        self._stepgens.setValue(m.num_stepgens)
        self._pwmgens.setValue(m.num_pwmgens)
        self._sserial_n.setValue(m.num_smart_serial)
        self._ss_chans.setValue(m.num_smart_serial_channels)

        self._cb_7i29.setChecked(m.check_7i29)
        self._cb_7i30.setChecked(m.check_7i30)
        self._cb_7i33.setChecked(m.check_7i33)
        self._cb_7i40.setChecked(m.check_7i40)
        self._cb_7i48.setChecked(m.check_7i48)

        self._on_sserial_count_changed(m.num_smart_serial)

        # Restore smart serial channel allocations
        if m.sserial_channels and self._ss_table.rowCount() > 0:
            for i, ch_cfg in enumerate(m.sserial_channels):
                if i >= self._ss_table.rowCount():
                    break
                dev_w = self._ss_table.cellWidget(i, 1)
                adr_w = self._ss_table.cellWidget(i, 2)
                if dev_w:
                    dev_w.setCurrentText(ch_cfg.device)
                if adr_w:
                    adr_w.setValue(ch_cfg.device_address)

    def save(self, cfg: MachineConfig):
        from config.machine_config import SmartSerialChannel
        m = cfg.mesa
        m.board_name               = self._board.currentText()
        m.firmware                 = self._firmware.currentText()
        m.ip_address               = self._card_addr.text().strip()
        m.pwm_base_freq            = self._pwm_freq.value()
        m.pdm_base_freq            = self._pdm_freq.value()
        m.watchdog_timeout         = self._watchdog.value()
        m.num_encoders             = self._encoders.value()
        m.num_stepgens             = self._stepgens.value()
        m.num_pwmgens              = self._pwmgens.value()
        m.num_smart_serial         = self._sserial_n.value()
        m.num_smart_serial_channels = self._ss_chans.value()

        m.check_7i29 = self._cb_7i29.isChecked()
        m.check_7i30 = self._cb_7i30.isChecked()
        m.check_7i33 = self._cb_7i33.isChecked()
        m.check_7i40 = self._cb_7i40.isChecked()
        m.check_7i48 = self._cb_7i48.isChecked()

        # Save smart serial channel allocation
        m.sserial_channels = []
        for row in range(self._ss_table.rowCount()):
            dev_w = self._ss_table.cellWidget(row, 1)
            adr_w = self._ss_table.cellWidget(row, 2)
            m.sserial_channels.append(SmartSerialChannel(
                channel_num=row,
                device=dev_w.currentText() if dev_w else "Unused",
                device_address=adr_w.value() if adr_w else 0,
            ))

        # Update connectors for new board/firmware
        m.update_from_firmware()

    def validate(self):
        board = self._board.currentText()
        fw    = self._firmware.currentText()
        if not fw:
            return False, "No firmware selected."
        from config.machine_config import get_firmware_spec
        spec = get_firmware_spec(board, fw)
        if spec is None:
            # Custom firmware — warn but allow
            pass
        # Check watchdog vs a sane minimum
        if self._watchdog.value() < 1.0:
            return False, "Watchdog timeout must be ≥ 1.0 ms."
        return True, ""
