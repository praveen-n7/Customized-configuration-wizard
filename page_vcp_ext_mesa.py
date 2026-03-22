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
    )
    from PyQt6.QtCore import Qt
except ImportError:
    from PySide6.QtWidgets import (
        QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit,
        QComboBox, QSpinBox, QDoubleSpinBox, QGroupBox, QCheckBox,
        QPushButton, QFileDialog, QFrame, QScrollArea, QWidget,
        QTabWidget, QRadioButton, QButtonGroup,
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


# ─────────────────────────────────────────────────────────────────────────────
# EXTERNAL CONTROLS PAGE
# ─────────────────────────────────────────────────────────────────────────────

class ExternalControlsPage(BasePage):
    PAGE_TITLE    = "External Controls"
    PAGE_SUBTITLE = "Configure external jogging, MPG, VFD, and override devices"

    VFD_DRIVERS = ["gs2", "vfs11", "hy_vfd", "abb_badvfd", "smc_gs2"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        inner = QWidget()
        root = QVBoxLayout(inner)
        root.setContentsMargins(32, 24, 32, 24)
        root.setSpacing(16)

        # Split layout: left panel (checkboxes) + right tab panel
        h = QHBoxLayout()
        h.setSpacing(16)
        h.addWidget(self._build_left_panel(), stretch=0)
        h.addWidget(self._build_right_tabs(), stretch=1)
        root.addLayout(h)
        root.addStretch()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(_scroll_page(inner))

    # ── Left panel — enable checkboxes ────────────────────────────────────────
    def _build_left_panel(self) -> QGroupBox:
        grp = QGroupBox("Enable Controls")
        grp.setFixedWidth(220)
        v = QVBoxLayout(grp)
        v.setSpacing(8)

        self._cb_vfd         = QCheckBox("Serial VFD")
        self._cb_btn_jog     = QCheckBox("External Button Jogging")
        self._cb_mpg         = QCheckBox("External MPG Jogging")
        self._cb_feed_ovr    = QCheckBox("External Feed Override")
        self._cb_max_vel_ovr = QCheckBox("Max Velocity Override")
        self._cb_spindle_ovr = QCheckBox("Spindle Override")
        self._cb_usb_jog     = QCheckBox("USB Jogging")

        for cb in [self._cb_vfd, self._cb_btn_jog, self._cb_mpg,
                   self._cb_feed_ovr, self._cb_max_vel_ovr,
                   self._cb_spindle_ovr, self._cb_usb_jog]:
            v.addWidget(cb)

        v.addStretch()
        return grp

    # ── Right panel — tabbed detail ───────────────────────────────────────────
    def _build_right_tabs(self) -> QTabWidget:
        self._tabs = QTabWidget()

        self._tabs.addTab(self._build_tab_vfd(),        "VFD")
        self._tabs.addTab(self._build_tab_btn_jog(),    "Button Jog")
        self._tabs.addTab(self._build_tab_mpg(),        "MPG")
        self._tabs.addTab(self._build_tab_joy_jog(),    "Joy Jog")
        self._tabs.addTab(self._build_tab_fo(),         "FO")
        self._tabs.addTab(self._build_tab_mvo(),        "MVO")
        self._tabs.addTab(self._build_tab_so(),         "SO")
        self._tabs.addTab(self._build_tab_text(),       "Text")

        # Wire checkboxes to enable/disable tabs
        self._cb_vfd.toggled.connect(
            lambda en: self._tabs.setTabEnabled(0, en))
        self._cb_btn_jog.toggled.connect(
            lambda en: self._tabs.setTabEnabled(1, en))
        self._cb_mpg.toggled.connect(
            lambda en: self._tabs.setTabEnabled(2, en))
        self._cb_usb_jog.toggled.connect(
            lambda en: self._tabs.setTabEnabled(3, en))
        self._cb_feed_ovr.toggled.connect(
            lambda en: self._tabs.setTabEnabled(4, en))
        self._cb_max_vel_ovr.toggled.connect(
            lambda en: self._tabs.setTabEnabled(5, en))
        self._cb_spindle_ovr.toggled.connect(
            lambda en: self._tabs.setTabEnabled(6, en))

        # Disable all detail tabs initially
        for i in range(7):
            self._tabs.setTabEnabled(i, False)

        return self._tabs

    # Tab: VFD ─────────────────────────────────────────────────────────────────
    def _build_tab_vfd(self) -> QWidget:
        w = QWidget()
        g = QGridLayout(w)
        g.setContentsMargins(16, 16, 16, 16)
        g.setHorizontalSpacing(16)
        g.setVerticalSpacing(10)

        self._vfd_driver = QComboBox()
        self._vfd_driver.addItems(self.VFD_DRIVERS)
        g.addWidget(QLabel("VFD Driver:"), 0, 0)
        g.addWidget(self._vfd_driver, 0, 1)

        hint = QLabel(
            "gs2: Automation Direct GS2 series\n"
            "vfs11: Toshiba VFS11\n"
            "hy_vfd: Huanyang VFD\n"
            "abb_badvfd: ABB VFD (bad)\n"
            "smc_gs2: SMC clone of GS2"
        )
        hint.setStyleSheet(_HINT)
        g.addWidget(hint, 1, 0, 1, 2)
        g.setRowStretch(2, 1)
        return w

    # Tab: Button Jog ──────────────────────────────────────────────────────────
    def _build_tab_btn_jog(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(16, 16, 16, 16)
        v.addWidget(QLabel("External button jogging uses digital inputs"))
        v.addWidget(QLabel("configured on the connectors page."))
        info = QLabel("Assign 'jog+' and 'jog-' signals on the I/O connector page.")
        info.setStyleSheet(_HINT)
        info.setWordWrap(True)
        v.addWidget(info)
        v.addStretch()
        return w

    # Tab: MPG ─────────────────────────────────────────────────────────────────
    def _build_tab_mpg(self) -> QWidget:
        w = QWidget()
        g = QGridLayout(w)
        g.setContentsMargins(16, 16, 16, 16)
        g.setHorizontalSpacing(16)
        g.setVerticalSpacing(10)

        self._mpg_increments = QLineEdit()
        self._mpg_increments.setPlaceholderText("0.1 0.01 0.001")
        self._mpg_increments.setToolTip(
            "Space-separated step sizes for MPG. "
            "Each click of the MPG wheel moves by the selected increment."
        )
        g.addWidget(QLabel("MPG Increments:"), 0, 0)
        g.addWidget(self._mpg_increments, 0, 1)

        hint = QLabel(
            "MPG (Manual Pulse Generator) uses a quadrature encoder input.\n"
            "Assign 'mpg-a' and 'mpg-b' signals on the connector page."
        )
        hint.setStyleSheet(_HINT)
        hint.setWordWrap(True)
        g.addWidget(hint, 1, 0, 1, 2)
        g.setRowStretch(2, 1)
        return w

    # Tab: Joy Jog (USB) ───────────────────────────────────────────────────────
    def _build_tab_joy_jog(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(16, 16, 16, 16)
        lbl = QLabel(
            "USB joystick jogging uses the LinuxCNC input component.\n"
            "Configure axis mappings in the generated HAL file."
        )
        lbl.setWordWrap(True)
        v.addWidget(lbl)
        v.addStretch()
        return w

    # Tab: FO (Feed Override) ──────────────────────────────────────────────────
    def _build_tab_fo(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(16, 16, 16, 16)
        lbl = QLabel(
            "External Feed Override uses an analog or encoder input.\n"
            "Assign the 'feed-override' signal on the connector page."
        )
        lbl.setWordWrap(True)
        v.addWidget(lbl)
        v.addStretch()
        return w

    # Tab: MVO (Max Velocity Override) ─────────────────────────────────────────
    def _build_tab_mvo(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(16, 16, 16, 16)
        lbl = QLabel(
            "External Max Velocity Override uses an analog or encoder input.\n"
            "Assign the 'max-velocity-override' signal on the connector page."
        )
        lbl.setWordWrap(True)
        v.addWidget(lbl)
        v.addStretch()
        return w

    # Tab: SO (Spindle Override) ───────────────────────────────────────────────
    def _build_tab_so(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(16, 16, 16, 16)
        lbl = QLabel(
            "External Spindle Override uses an analog or encoder input.\n"
            "Assign the 'spindle-override' signal on the connector page."
        )
        lbl.setWordWrap(True)
        v.addWidget(lbl)
        v.addStretch()
        return w

    # Tab: Text (notes / HAL snippet preview) ──────────────────────────────────
    def _build_tab_text(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(16, 16, 16, 16)
        lbl = QLabel(
            "Enable controls on the left to configure each device.\n"
            "HAL snippets are generated automatically when the config is exported."
        )
        lbl.setWordWrap(True)
        v.addWidget(lbl)
        v.addStretch()
        return w

    # ── populate / save ───────────────────────────────────────────────────────
    def populate(self, cfg: MachineConfig):
        e = cfg.external

        self._cb_vfd.setChecked(e.use_serial_vfd)
        self._cb_btn_jog.setChecked(e.use_ext_button_jogging)
        self._cb_mpg.setChecked(e.use_mpg)
        self._cb_feed_ovr.setChecked(e.use_feed_override)
        self._cb_max_vel_ovr.setChecked(e.use_max_vel_override)
        self._cb_spindle_ovr.setChecked(e.use_spindle_override)
        self._cb_usb_jog.setChecked(e.use_usb_jogging)

        self._vfd_driver.setCurrentText(e.vfd.driver)
        self._mpg_increments.setText(e.mpg.increments)

    def save(self, cfg: MachineConfig):
        e = cfg.external

        e.use_serial_vfd        = self._cb_vfd.isChecked()
        e.use_ext_button_jogging = self._cb_btn_jog.isChecked()
        e.use_mpg               = self._cb_mpg.isChecked()
        e.use_feed_override     = self._cb_feed_ovr.isChecked()
        e.use_max_vel_override  = self._cb_max_vel_ovr.isChecked()
        e.use_spindle_override  = self._cb_spindle_ovr.isChecked()
        e.use_usb_jogging       = self._cb_usb_jog.isChecked()

        e.vfd.enabled           = e.use_serial_vfd
        e.vfd.driver            = self._vfd_driver.currentText()
        e.mpg.enabled           = e.use_mpg
        e.mpg.increments        = self._mpg_increments.text().strip() or "0.1 0.01 0.001"

        # Keep legacy fields in sync
        cfg.spindle.vfd_type    = e.vfd.driver if e.use_serial_vfd else "none"
        e.use_ext_jogging       = e.use_ext_button_jogging
        e.mpg_increments        = e.mpg.increments


# ─────────────────────────────────────────────────────────────────────────────
# MESA CARD CONFIGURATION PAGE  (unchanged from original — preserved as-is)
# ─────────────────────────────────────────────────────────────────────────────

class MesaConfigPage(BasePage):
    PAGE_TITLE    = "Mesa Card Configuration"
    PAGE_SUBTITLE = "Configure Mesa FPGA board firmware and signal parameters"

    FIRMWARES = {
        "5i25":  ["5i25_prob_rf.bit", "5i25_sserial.bit", "5i25_t7i76d.bit"],
        "7i76e": ["7i76e.bit", "7i76e_7i76.bit"],
        "7i92":  ["7i92_5abcg20.bit", "7i92_7i76x2.bit"],
        "7i96":  ["7i96.bit", "7i96_s.bit"],
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 24, 32, 24)
        root.setSpacing(16)

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

        ch_group = QGroupBox("Channel Counts")
        ch_grid = QGridLayout(ch_group)
        ch_grid.setHorizontalSpacing(16)
        ch_grid.setVerticalSpacing(10)

        self._encoders = QSpinBox(); self._encoders.setRange(0, 32); self._encoders.setValue(1)
        ch_grid.addWidget(QLabel("Encoders:"), 0, 0); ch_grid.addWidget(self._encoders, 0, 1)

        self._stepgens = QSpinBox(); self._stepgens.setRange(0, 32); self._stepgens.setValue(5)
        ch_grid.addWidget(QLabel("Step Generators:"), 1, 0); ch_grid.addWidget(self._stepgens, 1, 1)

        self._smart_serial = QSpinBox(); self._smart_serial.setRange(0, 8)
        ch_grid.addWidget(QLabel("Smart Serial Ports:"), 2, 0); ch_grid.addWidget(self._smart_serial, 2, 1)

        root.addWidget(ch_group)
        root.addStretch()

        self._update_firmware_list(self._board.currentText())

    def _update_firmware_list(self, board: str):
        self._firmware.clear()
        self._firmware.addItems(self.FIRMWARES.get(board, [f"{board}.bit"]))

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
        m.board_name         = self._board.currentText()
        m.firmware           = self._firmware.currentText()
        m.pwm_base_freq      = self._pwm_freq.value()
        m.pdm_base_freq      = self._pdm_freq.value()
        m.watchdog_timeout   = self._watchdog.value()
        m.num_encoders       = self._encoders.value()
        m.num_stepgens       = self._stepgens.value()
        m.num_smart_serial   = self._smart_serial.value()
