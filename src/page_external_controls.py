"""
External Controls Page — Full Feature Parity
=============================================
Exact behavioral replication of the original LinuxCNC GTK PnCConf
External Controls page.

Layout:
  ┌───────────────────────┬──────────────────────────────────────────┐
  │  Left panel           │  Right tab panel                         │
  │  (enable checkboxes)  │  VFD | Btn Jog | MPG | Joy | FO | MVO   │
  │                       │  | SO | Text                             │
  └───────────────────────┴──────────────────────────────────────────┘

Each checkbox enables exactly one tab.  All tab contents are fully
wired widgets — no placeholders.
"""
from __future__ import annotations

try:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
        QLabel, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox,
        QGroupBox, QCheckBox, QPushButton, QFrame,
        QScrollArea, QTabWidget, QRadioButton, QButtonGroup,
        QTableWidget, QTableWidgetItem, QHeaderView, QSizePolicy,
        QAbstractItemView,
    )
    from PyQt6.QtCore import Qt, pyqtSignal as Signal
    from PyQt6.QtGui import QFont
except ImportError:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
        QLabel, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox,
        QGroupBox, QCheckBox, QPushButton, QFrame,
        QScrollArea, QTabWidget, QRadioButton, QButtonGroup,
        QTableWidget, QTableWidgetItem, QHeaderView, QSizePolicy,
        QAbstractItemView,
    )
    from PySide6.QtCore import Qt, Signal
    from PySide6.QtGui import QFont

from pages.base_page import BasePage
from config.machine_config import MachineConfig
from config.ext_controls_config import (
    ExternalControlsConfig, VFDConfig, ButtonJogConfig,
    ButtonJogAxisConfig, MPGConfig, MPGIncrementRow,
    JoyJogConfig, JoyJogAxisMapping, OverrideConfig,
    _default_mpg_increments,
)

# ── Style helpers ─────────────────────────────────────────────────────────────
_HINT  = "color: #4C566A; font-size: 8.5pt;"
_MONO  = "font-family: monospace; font-size: 9pt; color: #A3BE8C;"
_WARN  = "color: #EBCB8B; font-size: 8.5pt;"
_AXES  = ["X", "Y", "Z", "A", "B", "C"]


def _dbl(lo: float, hi: float, val: float, dec: int = 3,
         suffix: str = "") -> QDoubleSpinBox:
    s = QDoubleSpinBox()
    s.setRange(lo, hi)
    s.setDecimals(dec)
    s.setValue(val)
    if suffix:
        s.setSuffix(suffix)
    return s


def _int(lo: int, hi: int, val: int, suffix: str = "") -> QSpinBox:
    s = QSpinBox()
    s.setRange(lo, hi)
    s.setValue(val)
    if suffix:
        s.setSuffix(suffix)
    return s


def _combo(items, current="") -> QComboBox:
    c = QComboBox()
    c.addItems(items)
    if current:
        c.setCurrentText(current)
    return c


def _hline() -> QFrame:
    f = QFrame()
    f.setFrameShape(QFrame.Shape.HLine)
    f.setStyleSheet("color: #3A3A50;")
    return f


def _hint(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setWordWrap(True)
    lbl.setStyleSheet(_HINT)
    return lbl


def _section_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(
        "color: #81A1C1; font-weight: 600; font-size: 9pt; "
        "border-bottom: 1px solid #3A3A50; padding-bottom: 2px;"
    )
    return lbl


def _pin_edit(placeholder: str = "") -> QLineEdit:
    e = QLineEdit()
    e.setPlaceholderText(placeholder or "HAL pin name")
    e.setFont(QFont("monospace"))
    e.setStyleSheet(_MONO)
    return e


def _scroll(widget: QWidget) -> QScrollArea:
    sc = QScrollArea()
    sc.setWidgetResizable(True)
    sc.setFrameShape(QFrame.Shape.NoFrame)
    sc.setWidget(widget)
    return sc


# ─────────────────────────────────────────────────────────────────────────────
# Tab index constants
# ─────────────────────────────────────────────────────────────────────────────
_TAB_VFD   = 0
_TAB_BTNJOG = 1
_TAB_MPG   = 2
_TAB_JOY   = 3
_TAB_FO    = 4
_TAB_MVO   = 5
_TAB_SO    = 6
_TAB_TEXT  = 7


# ─────────────────────────────────────────────────────────────────────────────
# External Controls Page
# ─────────────────────────────────────────────────────────────────────────────

class ExternalControlsPage(BasePage):
    PAGE_TITLE    = "External Controls"
    PAGE_SUBTITLE = "Configure external jogging, MPG, VFD, and override devices"

    # ── Init ──────────────────────────────────────────────────────────────────

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self._connect_signals()

    # ── UI Assembly ───────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_left_panel(), stretch=0)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.VLine)
        divider.setStyleSheet("color: #3A3A50;")
        root.addWidget(divider)

        root.addWidget(self._build_right_tabs(), stretch=1)

    # ═════════════════════════════════════════════════════════════════════════
    # LEFT PANEL
    # ═════════════════════════════════════════════════════════════════════════

    def _build_left_panel(self) -> QWidget:
        frame = QFrame()
        frame.setFixedWidth(230)
        frame.setStyleSheet("background-color: #1E1E2E;")

        outer = QVBoxLayout(frame)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        hdr = QLabel("  Enable Controls")
        hdr.setStyleSheet(
            "background-color: #16162A; color: #5E81AC; "
            "font-weight: 700; font-size: 9pt; padding: 10px 16px; "
            "border-bottom: 1px solid #3A3A50; letter-spacing: 0.5px;"
        )
        outer.addWidget(hdr)

        scroll_inner = QWidget()
        v = QVBoxLayout(scroll_inner)
        v.setContentsMargins(16, 12, 16, 12)
        v.setSpacing(4)

        cb_defs = [
            ("_cb_vfd",      _TAB_VFD,    "Serial VFD"),
            ("_cb_btn_jog",  _TAB_BTNJOG, "External Button Jogging"),
            ("_cb_mpg",      _TAB_MPG,    "External MPG Jogging"),
            ("_cb_feed_ovr", _TAB_FO,     "External Feed Override"),
            ("_cb_max_vel",  _TAB_MVO,    "Max Velocity Override"),
            ("_cb_spin_ovr", _TAB_SO,     "Spindle Override"),
            ("_cb_usb_jog",  _TAB_JOY,    "USB Jogging"),
        ]
        self._cb_tab_map: dict[QCheckBox, int] = {}

        for attr, tab_idx, label in cb_defs:
            cb = QCheckBox(label)
            cb.setStyleSheet(
                "QCheckBox { color: #ECEFF4; font-size: 9.5pt; "
                "padding: 6px 4px; border-radius: 4px; }"
                "QCheckBox:hover { background-color: #252538; }"
            )
            setattr(self, attr, cb)
            self._cb_tab_map[cb] = tab_idx
            v.addWidget(cb)

        v.addStretch()

        sc = _scroll(scroll_inner)
        outer.addWidget(sc)
        return frame

    # ═════════════════════════════════════════════════════════════════════════
    # RIGHT TABS
    # ═════════════════════════════════════════════════════════════════════════

    def _build_right_tabs(self) -> QTabWidget:
        self._tabs = QTabWidget()

        tabs = [
            (_TAB_VFD,    "VFD",       self._build_tab_vfd()),
            (_TAB_BTNJOG, "Button Jog",self._build_tab_btn_jog()),
            (_TAB_MPG,    "MPG",       self._build_tab_mpg()),
            (_TAB_JOY,    "Joy Jog",   self._build_tab_joy_jog()),
            (_TAB_FO,     "FO",        self._build_tab_override(
                                           "fo", "Feed Override",
                                           "halui.feed-override.scale")),
            (_TAB_MVO,    "MVO",       self._build_tab_override(
                                           "mvo", "Max Velocity Override",
                                           "halui.max-velocity.value")),
            (_TAB_SO,     "SO",        self._build_tab_override(
                                           "so", "Spindle Override",
                                           "halui.spindle.0.override.scale")),
            (_TAB_TEXT,   "Text",      self._build_tab_text()),
        ]

        for idx, label, widget in tabs:
            self._tabs.addTab(widget, label)

        # All detail tabs start disabled
        for i in range(_TAB_TEXT):
            self._tabs.setTabEnabled(i, False)

        return self._tabs

    # ═════════════════════════════════════════════════════════════════════════
    # TAB: VFD
    # ═════════════════════════════════════════════════════════════════════════

    def _build_tab_vfd(self) -> QWidget:
        inner = QWidget()
        root = QVBoxLayout(inner)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        # ── Driver ────────────────────────────────────────────────────────────
        root.addWidget(_section_label("Driver"))
        g1 = QGridLayout()
        g1.setHorizontalSpacing(16)
        g1.setVerticalSpacing(8)

        self._vfd_driver = _combo(
            ["gs2", "vfs11", "hy_vfd", "abb_badvfd", "smc_gs2"],
            "gs2"
        )
        g1.addWidget(QLabel("VFD Driver:"), 0, 0)
        g1.addWidget(self._vfd_driver, 0, 1)
        g1.addWidget(_hint("gs2: GS2 series  |  vfs11: Toshiba VFS11  |  hy_vfd: Huanyang"), 1, 0, 1, 3)

        root.addLayout(g1)
        root.addWidget(_hline())

        # ── Serial Port ───────────────────────────────────────────────────────
        root.addWidget(_section_label("Serial Port"))
        g2 = QGridLayout()
        g2.setHorizontalSpacing(16)
        g2.setVerticalSpacing(8)

        self._vfd_device = _pin_edit("/dev/ttyS0")
        self._vfd_device.setPlaceholderText("/dev/ttyS0  or  /dev/ttyUSB0")
        g2.addWidget(QLabel("Device:"), 0, 0)
        g2.addWidget(self._vfd_device, 0, 1)

        self._vfd_baud = _combo(
            ["1200", "2400", "4800", "9600", "19200", "38400", "57600", "115200"],
            "9600"
        )
        g2.addWidget(QLabel("Baud Rate:"), 1, 0)
        g2.addWidget(self._vfd_baud, 1, 1)

        self._vfd_stop_bits = _combo(["1", "2"], "1")
        g2.addWidget(QLabel("Stop Bits:"), 2, 0)
        g2.addWidget(self._vfd_stop_bits, 2, 1)

        self._vfd_parity = _combo(["none", "even", "odd"], "none")
        g2.addWidget(QLabel("Parity:"), 3, 0)
        g2.addWidget(self._vfd_parity, 3, 1)

        self._vfd_slave = _int(1, 247, 1)
        g2.addWidget(QLabel("Slave Address:"), 4, 0)
        g2.addWidget(self._vfd_slave, 4, 1)

        root.addLayout(g2)
        root.addWidget(_hline())

        # ── Ramp Times ────────────────────────────────────────────────────────
        root.addWidget(_section_label("Ramp Times"))
        g3 = QGridLayout()
        g3.setHorizontalSpacing(16)
        g3.setVerticalSpacing(8)

        self._vfd_accel = _dbl(0.1, 300.0, 5.0, 1, " s")
        g3.addWidget(QLabel("Acceleration Time:"), 0, 0)
        g3.addWidget(self._vfd_accel, 0, 1)

        self._vfd_decel = _dbl(0.1, 300.0, 5.0, 1, " s")
        g3.addWidget(QLabel("Deceleration Time:"), 1, 0)
        g3.addWidget(self._vfd_decel, 1, 1)

        self._vfd_at_speed_tol = _dbl(0.0, 1.0, 0.1, 3)
        g3.addWidget(QLabel("At-Speed Tolerance:"), 2, 0)
        g3.addWidget(self._vfd_at_speed_tol, 2, 1)
        g3.addWidget(_hint("Fraction of commanded speed (e.g. 0.1 = ±10%)"), 2, 2)

        root.addLayout(g3)
        root.addWidget(_hline())

        # ── HAL Signal Names ──────────────────────────────────────────────────
        root.addWidget(_section_label("HAL Signal Names (advanced)"))
        g4 = QGridLayout()
        g4.setHorizontalSpacing(16)
        g4.setVerticalSpacing(8)

        self._vfd_hal_speed  = _pin_edit("spindle.0.speed-out-rps")
        self._vfd_hal_enable = _pin_edit("spindle.0.on")
        self._vfd_hal_fwd    = _pin_edit("spindle.0.forward")
        self._vfd_hal_rev    = _pin_edit("spindle.0.reverse")

        for row, (label, w) in enumerate([
            ("Speed-in pin:",  self._vfd_hal_speed),
            ("Enable pin:",    self._vfd_hal_enable),
            ("Forward pin:",   self._vfd_hal_fwd),
            ("Reverse pin:",   self._vfd_hal_rev),
        ]):
            g4.addWidget(QLabel(label), row, 0)
            g4.addWidget(w, row, 1)

        root.addLayout(g4)
        root.addStretch()

        return _scroll(inner)

    # ═════════════════════════════════════════════════════════════════════════
    # TAB: BUTTON JOG
    # ═════════════════════════════════════════════════════════════════════════

    def _build_tab_btn_jog(self) -> QWidget:
        inner = QWidget()
        root = QVBoxLayout(inner)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        # ── Shared speeds ─────────────────────────────────────────────────────
        root.addWidget(_section_label("Jog Speeds"))
        g_speed = QGridLayout()
        g_speed.setHorizontalSpacing(16)
        g_speed.setVerticalSpacing(8)

        self._btnjog_slow = _dbl(0.1, 10000.0, 100.0, 1, " mm/min")
        self._btnjog_fast = _dbl(0.1, 10000.0, 1000.0, 1, " mm/min")
        g_speed.addWidget(QLabel("Slow Jog Speed:"), 0, 0)
        g_speed.addWidget(self._btnjog_slow, 0, 1)
        g_speed.addWidget(QLabel("Fast Jog Speed:"), 1, 0)
        g_speed.addWidget(self._btnjog_fast, 1, 1)

        self._btnjog_use_fast = QCheckBox("Use separate Fast button")
        g_speed.addWidget(self._btnjog_use_fast, 2, 0, 1, 2)

        self._btnjog_fast_pin = _pin_edit("GPIO pin for fast-jog button")
        g_speed.addWidget(QLabel("Fast Button Pin:"), 3, 0)
        g_speed.addWidget(self._btnjog_fast_pin, 3, 1)
        self._btnjog_use_fast.toggled.connect(self._btnjog_fast_pin.setEnabled)
        self._btnjog_fast_pin.setEnabled(False)

        root.addLayout(g_speed)
        root.addWidget(_hline())

        # ── Per-axis configuration ─────────────────────────────────────────────
        root.addWidget(_section_label("Per-Axis Button Assignment"))

        self._btnjog_axis_widgets: dict[str, dict] = {}

        for ax in _AXES:
            grp = QGroupBox(f"Axis {ax}")
            gg = QGridLayout(grp)
            gg.setHorizontalSpacing(16)
            gg.setVerticalSpacing(6)

            enabled_cb = QCheckBox(f"Enable {ax} button jog")
            gg.addWidget(enabled_cb, 0, 0, 1, 3)

            pos_pin = _pin_edit(f"GPIO pin → jog {ax}+")
            neg_pin = _pin_edit(f"GPIO pin → jog {ax}−")
            inv_pos = QCheckBox("Invert")
            inv_neg = QCheckBox("Invert")
            spd     = _dbl(0.0, 10000.0, 0.0, 1, " mm/min")
            spd_lbl = QLabel("(0 = use global speed)")
            spd_lbl.setStyleSheet(_HINT)

            gg.addWidget(QLabel("+ Pin:"),     1, 0)
            gg.addWidget(pos_pin,              1, 1)
            gg.addWidget(inv_pos,              1, 2)
            gg.addWidget(QLabel("− Pin:"),     2, 0)
            gg.addWidget(neg_pin,              2, 1)
            gg.addWidget(inv_neg,              2, 2)
            gg.addWidget(QLabel("Axis Speed:"),3, 0)
            gg.addWidget(spd,                  3, 1)
            gg.addWidget(spd_lbl,              3, 2)

            def _wire(en_cb, *widgets):
                def _toggle(checked):
                    for w in widgets:
                        w.setEnabled(checked)
                en_cb.toggled.connect(_toggle)
                _toggle(False)
            _wire(enabled_cb, pos_pin, neg_pin, inv_pos, inv_neg, spd)

            self._btnjog_axis_widgets[ax] = {
                "enabled": enabled_cb,
                "pos_pin": pos_pin,
                "neg_pin": neg_pin,
                "inv_pos": inv_pos,
                "inv_neg": inv_neg,
                "speed":   spd,
            }
            root.addWidget(grp)

        root.addStretch()
        return _scroll(inner)

    # ═════════════════════════════════════════════════════════════════════════
    # TAB: MPG  (most complex)
    # ═════════════════════════════════════════════════════════════════════════

    def _build_tab_mpg(self) -> QWidget:
        inner = QWidget()
        root = QVBoxLayout(inner)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        # ── Mode ──────────────────────────────────────────────────────────────
        root.addWidget(_section_label("MPG Mode"))
        mode_box = QGroupBox()
        mode_box.setFlat(True)
        mode_v = QVBoxLayout(mode_box)
        mode_v.setSpacing(4)

        self._mpg_mode_group = QButtonGroup(mode_box)
        self._mpg_rb_mpg        = QRadioButton("Use MPG (quadrature encoder)")
        self._mpg_rb_switches   = QRadioButton("Use switches (digital inputs select direction + speed)")
        self._mpg_rb_increments = QRadioButton("Use increments table (switch combination → step size)")
        self._mpg_rb_mpg.setChecked(True)

        for rb in [self._mpg_rb_mpg, self._mpg_rb_switches, self._mpg_rb_increments]:
            self._mpg_mode_group.addButton(rb)
            mode_v.addWidget(rb)

        root.addWidget(mode_box)
        root.addWidget(_hline())

        # ── Encoder pins (MPG mode) ────────────────────────────────────────────
        self._mpg_enc_group = QGroupBox("Encoder Input Pins")
        ge = QGridLayout(self._mpg_enc_group)
        ge.setHorizontalSpacing(16)
        ge.setVerticalSpacing(8)

        self._mpg_enc_a   = _pin_edit("e.g. hm2_5i25.0.encoder.00.phase-A")
        self._mpg_enc_b   = _pin_edit("e.g. hm2_5i25.0.encoder.00.phase-B")
        self._mpg_enc_idx = _pin_edit("(optional) index pulse pin")

        for row, (lbl, w) in enumerate([
            ("Phase A:", self._mpg_enc_a),
            ("Phase B:", self._mpg_enc_b),
            ("Index:",   self._mpg_enc_idx),
        ]):
            ge.addWidget(QLabel(lbl), row, 0)
            ge.addWidget(w, row, 1)

        root.addWidget(self._mpg_enc_group)

        # ── Switch pins (switch/increments modes) ──────────────────────────────
        self._mpg_sw_group = QGroupBox("Switch Input Pins  (A / B / C / D)")
        gs = QGridLayout(self._mpg_sw_group)
        gs.setHorizontalSpacing(16)
        gs.setVerticalSpacing(8)

        self._mpg_sw_a = _pin_edit("Switch A pin")
        self._mpg_sw_b = _pin_edit("Switch B pin")
        self._mpg_sw_c = _pin_edit("Switch C pin")
        self._mpg_sw_d = _pin_edit("Switch D pin")

        for col, (lbl, w) in enumerate([
            ("A:", self._mpg_sw_a), ("B:", self._mpg_sw_b),
            ("C:", self._mpg_sw_c), ("D:", self._mpg_sw_d),
        ]):
            gs.addWidget(QLabel(lbl), 0, col * 2)
            gs.addWidget(w,           0, col * 2 + 1)

        root.addWidget(self._mpg_sw_group)

        # ── Increment table ────────────────────────────────────────────────────
        self._mpg_inc_group = QGroupBox("Increment Table")
        inc_v = QVBoxLayout(self._mpg_inc_group)

        self._mpg_table = QTableWidget(0, 8)
        self._mpg_table.setHorizontalHeaderLabels(
            ["a", "b", "c", "d", "ab", "bc", "abc", "Increment (units)"]
        )
        self._mpg_table.horizontalHeader().setSectionResizeMode(
            7, QHeaderView.ResizeMode.Stretch
        )
        for i in range(7):
            self._mpg_table.horizontalHeader().setSectionResizeMode(
                i, QHeaderView.ResizeMode.ResizeToContents
            )
        self._mpg_table.setMinimumHeight(150)
        self._mpg_table.setMaximumHeight(250)
        self._mpg_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )

        btn_row = QHBoxLayout()
        add_btn = QPushButton("Add Row")
        del_btn = QPushButton("Delete Row")
        add_btn.clicked.connect(self._mpg_add_row)
        del_btn.clicked.connect(self._mpg_del_row)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(del_btn)
        btn_row.addStretch()

        inc_v.addWidget(self._mpg_table)
        inc_v.addLayout(btn_row)

        root.addWidget(self._mpg_inc_group)

        # Populate table with defaults
        for row_data in _default_mpg_increments():
            self._mpg_add_row(row_data)

        # ── Axis selection ─────────────────────────────────────────────────────
        root.addWidget(_section_label("Axis Control"))
        g_ax = QGridLayout()
        g_ax.setHorizontalSpacing(16)
        g_ax.setVerticalSpacing(8)

        self._mpg_axis = _combo(["(use axis-select switches)"] + _AXES, "")
        g_ax.addWidget(QLabel("Controlled Axis:"), 0, 0)
        g_ax.addWidget(self._mpg_axis, 0, 1)

        self._mpg_velocity = _dbl(1.0, 10000.0, 100.0, 1, " mm/min")
        g_ax.addWidget(QLabel("Max Jog Velocity:"), 1, 0)
        g_ax.addWidget(self._mpg_velocity, 1, 1)

        self._mpg_scale = _dbl(0.001, 10000.0, 1.0, 4)
        g_ax.addWidget(QLabel("Scale (counts/unit):"), 2, 0)
        g_ax.addWidget(self._mpg_scale, 2, 1)

        root.addLayout(g_ax)

        # Axis-select switch pins (shown when axis = "use switches")
        self._mpg_ax_sel_group = QGroupBox("Axis-Select Switch Pins")
        gas = QGridLayout(self._mpg_ax_sel_group)
        gas.setHorizontalSpacing(16)
        gas.setVerticalSpacing(6)
        self._mpg_ax_sel_pins: dict[str, QLineEdit] = {}
        for col, ax in enumerate(_AXES):
            pin = _pin_edit(f"select {ax}")
            self._mpg_ax_sel_pins[ax] = pin
            gas.addWidget(QLabel(f"{ax}:"), 0, col * 2)
            gas.addWidget(pin,              0, col * 2 + 1)

        root.addWidget(self._mpg_ax_sel_group)
        root.addWidget(_hline())

        # ── Signal conditioning ───────────────────────────────────────────────
        root.addWidget(_section_label("Signal Conditioning"))
        g_sig = QGridLayout()
        g_sig.setHorizontalSpacing(16)
        g_sig.setVerticalSpacing(8)

        self._mpg_debounce = _dbl(0.0, 1.0, 0.0, 3, " s")
        g_sig.addWidget(QLabel("Debounce Time:"), 0, 0)
        g_sig.addWidget(self._mpg_debounce, 0, 1)
        g_sig.addWidget(_hint("0 = disabled"), 0, 2)

        self._mpg_gray    = QCheckBox("Use Gray code decoding")
        self._mpg_ignore  = QCheckBox("Ignore false inputs (glitch filter)")
        g_sig.addWidget(self._mpg_gray,   1, 0, 1, 3)
        g_sig.addWidget(self._mpg_ignore, 2, 0, 1, 3)

        root.addLayout(g_sig)
        root.addStretch()

        # ── Mode → show/hide sections ─────────────────────────────────────────
        def _mode_changed():
            is_mpg  = self._mpg_rb_mpg.isChecked()
            is_sw   = self._mpg_rb_switches.isChecked()
            is_inc  = self._mpg_rb_increments.isChecked()
            self._mpg_enc_group.setVisible(is_mpg)
            self._mpg_sw_group.setVisible(is_sw or is_inc)
            self._mpg_inc_group.setVisible(is_inc)
            self._mpg_ax_sel_group.setVisible(
                is_mpg and self._mpg_axis.currentIndex() == 0
            )

        self._mpg_rb_mpg.toggled.connect(_mode_changed)
        self._mpg_rb_switches.toggled.connect(_mode_changed)
        self._mpg_rb_increments.toggled.connect(_mode_changed)
        self._mpg_axis.currentIndexChanged.connect(_mode_changed)
        _mode_changed()

        return _scroll(inner)

    # ── MPG table helpers ──────────────────────────────────────────────────────

    def _mpg_add_row(self, row_data=None):
        row = self._mpg_table.rowCount()
        self._mpg_table.insertRow(row)

        if row_data is None:
            row_data = MPGIncrementRow()

        bool_cols = {"a": 0, "b": 1, "c": 2, "d": 3, "ab": 4, "bc": 5, "abc": 6}
        for attr, col in bool_cols.items():
            val = getattr(row_data, attr, False)
            item = QTableWidgetItem("1" if val else "0")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._mpg_table.setItem(row, col, item)

        inc_item = QTableWidgetItem(str(row_data.increment))
        inc_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._mpg_table.setItem(row, 7, inc_item)

    def _mpg_del_row(self):
        row = self._mpg_table.currentRow()
        if row >= 0:
            self._mpg_table.removeRow(row)

    def _mpg_read_table(self) -> list:
        rows = []
        for r in range(self._mpg_table.rowCount()):
            def _bool(col):
                item = self._mpg_table.item(r, col)
                return (item.text().strip() not in ("0", "", "False")) if item else False
            def _float(col):
                item = self._mpg_table.item(r, col)
                try:
                    return float(item.text()) if item else 0.001
                except ValueError:
                    return 0.001
            rows.append(MPGIncrementRow(
                a=_bool(0), b=_bool(1), c=_bool(2), d=_bool(3),
                ab=_bool(4), bc=_bool(5), abc=_bool(6),
                increment=_float(7),
            ))
        return rows

    # ═════════════════════════════════════════════════════════════════════════
    # TAB: JOY JOG
    # ═════════════════════════════════════════════════════════════════════════

    def _build_tab_joy_jog(self) -> QWidget:
        inner = QWidget()
        root = QVBoxLayout(inner)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        # ── Device ────────────────────────────────────────────────────────────
        root.addWidget(_section_label("Device"))
        g1 = QGridLayout()
        g1.setHorizontalSpacing(16)
        g1.setVerticalSpacing(8)

        self._joy_device = _pin_edit("/dev/input/js0")
        self._joy_device.setPlaceholderText("/dev/input/js0")
        g1.addWidget(QLabel("Device Path:"), 0, 0)
        g1.addWidget(self._joy_device, 0, 1)

        self._joy_hal_name = QLineEdit("joystick")
        g1.addWidget(QLabel("HAL Instance Name:"), 1, 0)
        g1.addWidget(self._joy_hal_name, 1, 1)

        root.addLayout(g1)
        root.addWidget(_hline())

        # ── Speed / Deadzone ──────────────────────────────────────────────────
        root.addWidget(_section_label("Speed & Sensitivity"))
        g2 = QGridLayout()
        g2.setHorizontalSpacing(16)
        g2.setVerticalSpacing(8)

        self._joy_max_speed = _dbl(1.0, 10000.0, 1000.0, 1, " mm/min")
        g2.addWidget(QLabel("Max Speed:"), 0, 0)
        g2.addWidget(self._joy_max_speed, 0, 1)

        self._joy_deadzone = _dbl(0.0, 0.99, 0.2, 2)
        g2.addWidget(QLabel("Deadzone:"), 1, 0)
        g2.addWidget(self._joy_deadzone, 1, 1)
        g2.addWidget(_hint("Fraction of full range below which input is treated as zero"), 1, 2)

        root.addLayout(g2)
        root.addWidget(_hline())

        # ── Axis Mappings ─────────────────────────────────────────────────────
        root.addWidget(_section_label("Axis Mappings"))
        self._joy_axis_widgets: list[dict] = []

        joy_axes_count = 6   # typical joystick
        for i in range(joy_axes_count):
            row_layout = QHBoxLayout()
            row_layout.setSpacing(10)

            row_layout.addWidget(QLabel(f"Joystick Axis {i}:"))
            machine_ax = _combo(["(none)"] + _AXES, "(none)")
            invert_cb  = QCheckBox("Invert")
            scale_sp   = _dbl(0.01, 100.0, 1.0, 3)
            row_layout.addWidget(machine_ax)
            row_layout.addWidget(QLabel("→"))
            row_layout.addWidget(invert_cb)
            row_layout.addWidget(QLabel("Scale:"))
            row_layout.addWidget(scale_sp)
            row_layout.addStretch()

            self._joy_axis_widgets.append({
                "machine": machine_ax,
                "invert":  invert_cb,
                "scale":   scale_sp,
            })
            root.addLayout(row_layout)

        # set defaults: axes 0→X, 1→Y, 2→Z
        defaults = ["X", "Y", "Z"]
        for i, ax in enumerate(defaults):
            self._joy_axis_widgets[i]["machine"].setCurrentText(ax)

        root.addWidget(_hline())

        # ── Button Mappings ────────────────────────────────────────────────────
        root.addWidget(_section_label("Button Mappings"))
        g3 = QGridLayout()
        g3.setHorizontalSpacing(16)
        g3.setVerticalSpacing(8)

        hal_funcs = [
            "(none)", "halui.estop.reset", "halui.home-all",
            "halui.program.run", "halui.program.stop",
            "halui.program.pause", "halui.machine.on", "halui.machine.off",
        ]
        self._joy_btn_widgets: list[QComboBox] = []
        for btn_idx in range(8):
            cb = _combo(hal_funcs, "(none)")
            cb.setEditable(True)
            g3.addWidget(QLabel(f"Button {btn_idx}:"), btn_idx, 0)
            g3.addWidget(cb, btn_idx, 1)
            self._joy_btn_widgets.append(cb)

        root.addLayout(g3)
        root.addStretch()

        return _scroll(inner)

    # ═════════════════════════════════════════════════════════════════════════
    # TAB: GENERIC OVERRIDE  (FO / MVO / SO share identical structure)
    # ═════════════════════════════════════════════════════════════════════════

    def _build_tab_override(self, prefix: str, label: str,
                             hal_target: str) -> QWidget:
        inner = QWidget()
        root = QVBoxLayout(inner)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        root.addWidget(_hint(
            f"HAL target: {hal_target}\n"
            f"This controls the {label} inside LinuxCNC."
        ))

        # ── Mode ──────────────────────────────────────────────────────────────
        root.addWidget(_section_label("Input Mode"))
        mode_grp = QButtonGroup(inner)
        rb_enc  = QRadioButton("Encoder (quadrature)")
        rb_ana  = QRadioButton("Analog (0–10 V)")
        rb_sw   = QRadioButton("Switch ladder")
        rb_enc.setChecked(True)
        for rb in [rb_enc, rb_ana, rb_sw]:
            mode_grp.addButton(rb)
            root.addWidget(rb)

        root.addWidget(_hline())

        # ── Encoder section ───────────────────────────────────────────────────
        enc_grp = QGroupBox("Encoder Pins")
        g_enc = QGridLayout(enc_grp)
        g_enc.setHorizontalSpacing(16)
        g_enc.setVerticalSpacing(8)

        enc_a = _pin_edit("phase-A pin")
        enc_b = _pin_edit("phase-B pin")
        cpr   = _int(1, 10000, 100, " cpr")

        g_enc.addWidget(QLabel("Phase A:"), 0, 0)
        g_enc.addWidget(enc_a, 0, 1)
        g_enc.addWidget(QLabel("Phase B:"), 1, 0)
        g_enc.addWidget(enc_b, 1, 1)
        g_enc.addWidget(QLabel("Counts/Rev:"), 2, 0)
        g_enc.addWidget(cpr, 2, 1)
        root.addWidget(enc_grp)

        # ── Analog section ────────────────────────────────────────────────────
        ana_grp = QGroupBox("Analog Input")
        g_ana = QGridLayout(ana_grp)
        g_ana.setHorizontalSpacing(16)
        g_ana.setVerticalSpacing(8)

        ana_pin  = _pin_edit("analog input pin")
        ana_min  = _dbl(0.0, 10.0, 0.0, 2, " V")
        ana_max  = _dbl(0.0, 10.0, 10.0, 2, " V")

        g_ana.addWidget(QLabel("Pin:"),      0, 0); g_ana.addWidget(ana_pin,  0, 1)
        g_ana.addWidget(QLabel("Min (V):"),  1, 0); g_ana.addWidget(ana_min,  1, 1)
        g_ana.addWidget(QLabel("Max (V):"),  2, 0); g_ana.addWidget(ana_max,  2, 1)
        root.addWidget(ana_grp)

        # ── Switch ladder section ─────────────────────────────────────────────
        sw_grp = QGroupBox("Switch Ladder  (each switch adds its value)")
        sw_v = QVBoxLayout(sw_grp)
        sw_table = QTableWidget(0, 2)
        sw_table.setHorizontalHeaderLabels(["Pin Name", "Value (fraction)"])
        sw_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        sw_table.setMaximumHeight(180)

        sw_add = QPushButton("Add Switch")
        sw_del = QPushButton("Remove")
        sw_btn_row = QHBoxLayout()
        sw_btn_row.addWidget(sw_add)
        sw_btn_row.addWidget(sw_del)
        sw_btn_row.addStretch()

        def _sw_add():
            r = sw_table.rowCount()
            sw_table.insertRow(r)
            sw_table.setItem(r, 0, QTableWidgetItem(""))
            sw_table.setItem(r, 1, QTableWidgetItem("0.1"))

        def _sw_del():
            row = sw_table.currentRow()
            if row >= 0:
                sw_table.removeRow(row)

        sw_add.clicked.connect(_sw_add)
        sw_del.clicked.connect(_sw_del)
        sw_v.addWidget(sw_table)
        sw_v.addLayout(sw_btn_row)
        root.addWidget(sw_grp)

        # ── Scaling ───────────────────────────────────────────────────────────
        root.addWidget(_hline())
        root.addWidget(_section_label("Scaling & Limits"))
        g_sc = QGridLayout()
        g_sc.setHorizontalSpacing(16)
        g_sc.setVerticalSpacing(8)

        min_val = _dbl(0.0, 2.0, 0.0, 3)
        max_val = _dbl(0.0, 5.0, 1.5, 3)
        scale   = _dbl(0.001, 100.0, 1.0, 4)
        filter_t = _dbl(0.0, 10.0, 0.0, 3, " s")
        debounce = _dbl(0.0, 1.0, 0.0, 3, " s")

        g_sc.addWidget(QLabel("Min value:"),    0, 0); g_sc.addWidget(min_val,  0, 1)
        g_sc.addWidget(QLabel("Max value:"),    1, 0); g_sc.addWidget(max_val,  1, 1)
        g_sc.addWidget(QLabel("Scale factor:"), 2, 0); g_sc.addWidget(scale,    2, 1)
        g_sc.addWidget(QLabel("Filter time:"),  3, 0); g_sc.addWidget(filter_t, 3, 1)
        g_sc.addWidget(_hint("0 = off"),        3, 2)
        g_sc.addWidget(QLabel("Debounce:"),     4, 0); g_sc.addWidget(debounce, 4, 1)
        g_sc.addWidget(_hint("switch-ladder mode only"), 4, 2)
        root.addLayout(g_sc)

        # ── HAL target (read-only info) ───────────────────────────────────────
        root.addWidget(_hline())
        root.addWidget(_section_label("HAL Target"))
        hal_lbl = QLabel(hal_target)
        hal_lbl.setStyleSheet(_MONO)
        root.addWidget(hal_lbl)
        root.addStretch()

        # Show/hide sections based on mode
        def _mode_sel():
            is_enc = rb_enc.isChecked()
            is_ana = rb_ana.isChecked()
            is_sw  = rb_sw.isChecked()
            enc_grp.setVisible(is_enc)
            ana_grp.setVisible(is_ana)
            sw_grp.setVisible(is_sw)

        rb_enc.toggled.connect(_mode_sel)
        rb_ana.toggled.connect(_mode_sel)
        rb_sw.toggled.connect(_mode_sel)
        _mode_sel()

        # Store widget refs by prefix so populate/save can access them
        attr = f"_ovr_{prefix}"
        setattr(self, attr, {
            "mode_enc": rb_enc, "mode_ana": rb_ana, "mode_sw": rb_sw,
            "enc_a": enc_a, "enc_b": enc_b, "cpr": cpr,
            "ana_pin": ana_pin, "ana_min": ana_min, "ana_max": ana_max,
            "sw_table": sw_table,
            "min_val": min_val, "max_val": max_val, "scale": scale,
            "filter_t": filter_t, "debounce": debounce,
        })

        return _scroll(inner)

    # ═════════════════════════════════════════════════════════════════════════
    # TAB: TEXT / Summary
    # ═════════════════════════════════════════════════════════════════════════

    def _build_tab_text(self) -> QWidget:
        inner = QWidget()
        root = QVBoxLayout(inner)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(12)

        root.addWidget(_section_label("Configuration Summary"))
        root.addWidget(_hint(
            "This tab shows a summary of enabled external controls.\n"
            "HAL snippets are generated automatically when you export the config."
        ))

        self._text_summary = QLabel()
        self._text_summary.setWordWrap(True)
        self._text_summary.setStyleSheet(
            "background-color: #16162A; border: 1px solid #3A3A50; "
            "border-radius: 4px; padding: 12px; font-family: monospace; "
            "font-size: 9pt; color: #A3BE8C;"
        )
        self._text_summary.setAlignment(Qt.AlignmentFlag.AlignTop)
        root.addWidget(self._text_summary, stretch=1)
        root.addStretch()
        return inner

    def _refresh_summary(self):
        lines = ["Enabled external controls:\n"]
        checks = [
            (self._cb_vfd,      "Serial VFD"),
            (self._cb_btn_jog,  "Button Jogging"),
            (self._cb_mpg,      "MPG"),
            (self._cb_feed_ovr, "Feed Override (FO)"),
            (self._cb_max_vel,  "Max Velocity Override (MVO)"),
            (self._cb_spin_ovr, "Spindle Override (SO)"),
            (self._cb_usb_jog,  "USB Joystick"),
        ]
        any_enabled = False
        for cb, label in checks:
            if cb.isChecked():
                lines.append(f"  ✓ {label}")
                any_enabled = True
        if not any_enabled:
            lines.append("  (none)")
        self._text_summary.setText("\n".join(lines))

    # ═════════════════════════════════════════════════════════════════════════
    # SIGNAL WIRING
    # ═════════════════════════════════════════════════════════════════════════

    def _connect_signals(self):
        for cb, tab_idx in self._cb_tab_map.items():
            cb.toggled.connect(
                lambda checked, i=tab_idx: self._tabs.setTabEnabled(i, checked)
            )
            cb.toggled.connect(self._refresh_summary)
            # Auto-switch to the newly enabled tab
            cb.toggled.connect(
                lambda checked, i=tab_idx: (
                    self._tabs.setCurrentIndex(i) if checked else None
                )
            )
        self._refresh_summary()

    # ═════════════════════════════════════════════════════════════════════════
    # populate() — load MachineConfig → widgets
    # ═════════════════════════════════════════════════════════════════════════

    def populate(self, cfg: MachineConfig):
        e: ExternalControlsConfig = cfg.external

        # Left panel checkboxes
        self._cb_vfd.setChecked(e.use_serial_vfd)
        self._cb_btn_jog.setChecked(e.use_ext_button_jogging)
        self._cb_mpg.setChecked(e.use_mpg)
        self._cb_feed_ovr.setChecked(e.use_feed_override)
        self._cb_max_vel.setChecked(e.use_max_vel_override)
        self._cb_spin_ovr.setChecked(e.use_spindle_override)
        self._cb_usb_jog.setChecked(e.use_usb_jogging)

        # VFD
        v = e.vfd
        self._vfd_driver.setCurrentText(v.driver)
        self._vfd_device.setText(v.device)
        self._vfd_baud.setCurrentText(str(v.baud))
        self._vfd_stop_bits.setCurrentText(str(v.stop_bits))
        self._vfd_parity.setCurrentText(v.parity)
        self._vfd_slave.setValue(v.slave)
        self._vfd_accel.setValue(v.accel_time)
        self._vfd_decel.setValue(v.decel_time)
        self._vfd_at_speed_tol.setValue(v.spindle_at_speed_tolerance)
        self._vfd_hal_speed.setText(v.hal_spindle_speed_in)
        self._vfd_hal_enable.setText(v.hal_spindle_enable)
        self._vfd_hal_fwd.setText(v.hal_spindle_fwd)
        self._vfd_hal_rev.setText(v.hal_spindle_rev)

        # Button Jog
        bj = e.button_jog
        self._btnjog_slow.setValue(bj.slow_speed)
        self._btnjog_fast.setValue(bj.fast_speed)
        self._btnjog_use_fast.setChecked(bj.use_fast_button)
        self._btnjog_fast_pin.setText(bj.fast_button_pin)
        for ax, w in self._btnjog_axis_widgets.items():
            ax_cfg = bj.axes.get(ax, ButtonJogAxisConfig())
            w["enabled"].setChecked(ax_cfg.enabled)
            w["pos_pin"].setText(ax_cfg.pin_positive)
            w["neg_pin"].setText(ax_cfg.pin_negative)
            w["inv_pos"].setChecked(ax_cfg.invert_positive)
            w["inv_neg"].setChecked(ax_cfg.invert_negative)
            w["speed"].setValue(ax_cfg.jog_speed)

        # MPG
        m = e.mpg
        if m.mode == "use_mpg":
            self._mpg_rb_mpg.setChecked(True)
        elif m.mode == "use_switches":
            self._mpg_rb_switches.setChecked(True)
        else:
            self._mpg_rb_increments.setChecked(True)

        self._mpg_enc_a.setText(m.encoder_a_pin)
        self._mpg_enc_b.setText(m.encoder_b_pin)
        self._mpg_enc_idx.setText(m.encoder_index_pin)
        self._mpg_sw_a.setText(m.switch_pin_a)
        self._mpg_sw_b.setText(m.switch_pin_b)
        self._mpg_sw_c.setText(m.switch_pin_c)
        self._mpg_sw_d.setText(m.switch_pin_d)

        # Reload increment table
        self._mpg_table.setRowCount(0)
        for row_data in (m.increment_table or _default_mpg_increments()):
            self._mpg_add_row(row_data)

        ax_text = m.mpg_axis if m.mpg_axis else "(use axis-select switches)"
        idx = self._mpg_axis.findText(ax_text)
        if idx >= 0:
            self._mpg_axis.setCurrentIndex(idx)

        self._mpg_velocity.setValue(m.jog_velocity)
        self._mpg_scale.setValue(m.scale)
        self._mpg_debounce.setValue(m.debounce_time)
        self._mpg_gray.setChecked(m.use_gray_code)
        self._mpg_ignore.setChecked(m.ignore_false_inputs)

        for ax, pin in m.axis_select_pins.items():
            if ax in self._mpg_ax_sel_pins:
                self._mpg_ax_sel_pins[ax].setText(pin)

        # Joy Jog
        j = e.joy_jog
        self._joy_device.setText(j.device)
        self._joy_hal_name.setText(j.hal_name)
        self._joy_max_speed.setValue(j.max_speed)
        self._joy_deadzone.setValue(j.deadzone)
        for i, mapping in enumerate(j.axis_mappings):
            if i < len(self._joy_axis_widgets):
                w = self._joy_axis_widgets[i]
                w["machine"].setCurrentText(mapping.machine_axis)
                w["invert"].setChecked(mapping.invert)
                w["scale"].setValue(mapping.scale)
        for btn_idx, func in j.button_map.items():
            if btn_idx < len(self._joy_btn_widgets):
                self._joy_btn_widgets[btn_idx].setCurrentText(func)

        # Override tabs
        self._populate_override("fo",  e.feed_override)
        self._populate_override("mvo", e.max_vel_override)
        self._populate_override("so",  e.spindle_override)

        self._refresh_summary()

    def _populate_override(self, prefix: str, ov: OverrideConfig):
        w = getattr(self, f"_ovr_{prefix}")
        if ov.mode == "encoder":
            w["mode_enc"].setChecked(True)
        elif ov.mode == "analog":
            w["mode_ana"].setChecked(True)
        else:
            w["mode_sw"].setChecked(True)
        w["enc_a"].setText(ov.encoder_a_pin)
        w["enc_b"].setText(ov.encoder_b_pin)
        w["cpr"].setValue(ov.counts_per_revolution)
        w["ana_pin"].setText(ov.analog_pin)
        w["ana_min"].setValue(ov.analog_min_voltage)
        w["ana_max"].setValue(ov.analog_max_voltage)
        w["min_val"].setValue(ov.min_value)
        w["max_val"].setValue(ov.max_value)
        w["scale"].setValue(ov.scale)
        w["filter_t"].setValue(ov.filter_time)
        w["debounce"].setValue(ov.debounce_time)
        # Switch ladder
        tbl: QTableWidget = w["sw_table"]
        tbl.setRowCount(0)
        for entry in ov.switch_ladder:
            r = tbl.rowCount()
            tbl.insertRow(r)
            tbl.setItem(r, 0, QTableWidgetItem(str(entry.get("pin", ""))))
            tbl.setItem(r, 1, QTableWidgetItem(str(entry.get("value", 0.1))))

    # ═════════════════════════════════════════════════════════════════════════
    # save() — widgets → MachineConfig
    # ═════════════════════════════════════════════════════════════════════════

    def save(self, cfg: MachineConfig):
        e: ExternalControlsConfig = cfg.external

        # Left-panel flags
        e.use_serial_vfd         = self._cb_vfd.isChecked()
        e.use_ext_button_jogging = self._cb_btn_jog.isChecked()
        e.use_mpg                = self._cb_mpg.isChecked()
        e.use_feed_override      = self._cb_feed_ovr.isChecked()
        e.use_max_vel_override   = self._cb_max_vel.isChecked()
        e.use_spindle_override   = self._cb_spin_ovr.isChecked()
        e.use_usb_jogging        = self._cb_usb_jog.isChecked()

        # VFD
        v = e.vfd
        v.enabled                    = e.use_serial_vfd
        v.driver                     = self._vfd_driver.currentText()
        v.device                     = self._vfd_device.text().strip() or "/dev/ttyS0"
        v.baud                       = int(self._vfd_baud.currentText())
        v.stop_bits                  = int(self._vfd_stop_bits.currentText())
        v.parity                     = self._vfd_parity.currentText()
        v.slave                      = self._vfd_slave.value()
        v.accel_time                 = self._vfd_accel.value()
        v.decel_time                 = self._vfd_decel.value()
        v.spindle_at_speed_tolerance = self._vfd_at_speed_tol.value()
        v.hal_spindle_speed_in       = self._vfd_hal_speed.text().strip()
        v.hal_spindle_enable         = self._vfd_hal_enable.text().strip()
        v.hal_spindle_fwd            = self._vfd_hal_fwd.text().strip()
        v.hal_spindle_rev            = self._vfd_hal_rev.text().strip()

        # Button Jog
        bj = e.button_jog
        bj.enabled         = e.use_ext_button_jogging
        bj.slow_speed      = self._btnjog_slow.value()
        bj.fast_speed      = self._btnjog_fast.value()
        bj.use_fast_button = self._btnjog_use_fast.isChecked()
        bj.fast_button_pin = self._btnjog_fast_pin.text().strip()
        for ax, w in self._btnjog_axis_widgets.items():
            if ax not in bj.axes:
                bj.axes[ax] = ButtonJogAxisConfig()
            ax_cfg                = bj.axes[ax]
            ax_cfg.enabled        = w["enabled"].isChecked()
            ax_cfg.pin_positive   = w["pos_pin"].text().strip()
            ax_cfg.pin_negative   = w["neg_pin"].text().strip()
            ax_cfg.invert_positive = w["inv_pos"].isChecked()
            ax_cfg.invert_negative = w["inv_neg"].isChecked()
            ax_cfg.jog_speed      = w["speed"].value()

        # MPG
        m = e.mpg
        m.enabled = e.use_mpg
        if self._mpg_rb_mpg.isChecked():
            m.mode = "use_mpg"
        elif self._mpg_rb_switches.isChecked():
            m.mode = "use_switches"
        else:
            m.mode = "use_increments"

        m.encoder_a_pin     = self._mpg_enc_a.text().strip()
        m.encoder_b_pin     = self._mpg_enc_b.text().strip()
        m.encoder_index_pin = self._mpg_enc_idx.text().strip()
        m.switch_pin_a      = self._mpg_sw_a.text().strip()
        m.switch_pin_b      = self._mpg_sw_b.text().strip()
        m.switch_pin_c      = self._mpg_sw_c.text().strip()
        m.switch_pin_d      = self._mpg_sw_d.text().strip()
        m.increment_table   = self._mpg_read_table()

        sel_text = self._mpg_axis.currentText()
        m.mpg_axis = "" if sel_text.startswith("(") else sel_text

        m.jog_velocity        = self._mpg_velocity.value()
        m.scale               = self._mpg_scale.value()
        m.debounce_time       = self._mpg_debounce.value()
        m.use_gray_code       = self._mpg_gray.isChecked()
        m.ignore_false_inputs = self._mpg_ignore.isChecked()

        for ax, pin_w in self._mpg_ax_sel_pins.items():
            m.axis_select_pins[ax] = pin_w.text().strip()

        # Joy Jog
        j = e.joy_jog
        j.enabled   = e.use_usb_jogging
        j.device    = self._joy_device.text().strip() or "/dev/input/js0"
        j.hal_name  = self._joy_hal_name.text().strip() or "joystick"
        j.max_speed = self._joy_max_speed.value()
        j.deadzone  = self._joy_deadzone.value()
        j.axis_mappings = []
        for i, w in enumerate(self._joy_axis_widgets):
            ax = w["machine"].currentText()
            if ax and ax != "(none)":
                j.axis_mappings.append(JoyJogAxisMapping(
                    machine_axis=ax,
                    joystick_axis=i,
                    invert=w["invert"].isChecked(),
                    scale=w["scale"].value(),
                ))
        j.button_map = {}
        for i, cb in enumerate(self._joy_btn_widgets):
            func = cb.currentText()
            if func and func != "(none)":
                j.button_map[i] = func

        # Override tabs
        self._save_override("fo",  e.feed_override)
        self._save_override("mvo", e.max_vel_override)
        self._save_override("so",  e.spindle_override)

        # Sync legacy fields
        e.sync_enabled_flags()
        cfg.spindle.vfd_type = v.driver if e.use_serial_vfd else "none"

    def _save_override(self, prefix: str, ov: OverrideConfig):
        w = getattr(self, f"_ovr_{prefix}")
        if w["mode_enc"].isChecked():
            ov.mode = "encoder"
        elif w["mode_ana"].isChecked():
            ov.mode = "analog"
        else:
            ov.mode = "switches"

        ov.encoder_a_pin          = w["enc_a"].text().strip()
        ov.encoder_b_pin          = w["enc_b"].text().strip()
        ov.counts_per_revolution  = w["cpr"].value()
        ov.analog_pin             = w["ana_pin"].text().strip()
        ov.analog_min_voltage     = w["ana_min"].value()
        ov.analog_max_voltage     = w["ana_max"].value()
        ov.min_value              = w["min_val"].value()
        ov.max_value              = w["max_val"].value()
        ov.scale                  = w["scale"].value()
        ov.filter_time            = w["filter_t"].value()
        ov.debounce_time          = w["debounce"].value()

        tbl: QTableWidget = w["sw_table"]
        ov.switch_ladder = []
        for r in range(tbl.rowCount()):
            pin_item = tbl.item(r, 0)
            val_item = tbl.item(r, 1)
            if pin_item:
                try:
                    val = float(val_item.text()) if val_item else 0.1
                except ValueError:
                    val = 0.1
                ov.switch_ladder.append({"pin": pin_item.text(), "value": val})

    def validate(self) -> tuple:
        # VFD: if enabled, device must be set
        if self._cb_vfd.isChecked():
            if not self._vfd_device.text().strip():
                return False, "VFD enabled but no device path specified."
        # MPG: if enabled, must have at least one encoder pin or switch pin
        if self._cb_mpg.isChecked():
            if self._mpg_rb_mpg.isChecked():
                if not self._mpg_enc_a.text().strip():
                    return False, "MPG enabled (encoder mode) but Phase A pin is not assigned."
        return True, ""
