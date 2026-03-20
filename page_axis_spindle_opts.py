"""
Axis Configuration Page
Spindle Configuration Page
Options Page
Realtime Components Page
"""
from __future__ import annotations

try:
    from PyQt6.QtWidgets import (
        QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
        QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox,
        QGroupBox, QCheckBox, QTabWidget, QWidget,
        QPushButton, QListWidget, QTextEdit,
    )
    from PyQt6.QtCore import Qt
except ImportError:
    from PySide6.QtWidgets import (
        QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
        QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox,
        QGroupBox, QCheckBox, QTabWidget, QWidget,
        QPushButton, QListWidget, QTextEdit,
    )
    from PySide6.QtCore import Qt

from pages.base_page import BasePage
from config.machine_config import MachineConfig, AxisConfig


# ─────────────────────────────────────────────────────────────────────────────
# Axis Configuration Page
# ─────────────────────────────────────────────────────────────────────────────

class AxisConfigPage(BasePage):
    PAGE_TITLE = "Axis Configuration"
    PAGE_SUBTITLE = "Set travel, home, and homing velocities per axis"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._axis_widgets: dict[str, dict] = {}
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 16, 24, 16)
        root.setSpacing(12)
        self._tabs = QTabWidget()
        root.addWidget(self._tabs)

    def _build_axis_tab(self, letter: str, ax: AxisConfig) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(14)
        ws: dict = {}

        # Travel
        travel_group = QGroupBox("Travel & Home Position")
        travel_grid = QGridLayout(travel_group)
        travel_grid.setHorizontalSpacing(16)
        travel_grid.setVerticalSpacing(10)

        for i, (label, attr, mn, mx, suffix) in enumerate([
            ("Travel Distance:",     "travel",              0.001, 10000, "mm"),
            ("Home Position:",       "home_position",       -9999, 9999,  "mm"),
            ("Home Switch Location:","home_switch_location",-9999, 9999,  "mm"),
        ]):
            spin = QDoubleSpinBox()
            spin.setRange(mn, mx)
            spin.setDecimals(4)
            spin.setValue(getattr(ax, attr))
            spin.setSuffix(f"  {suffix}")
            travel_grid.addWidget(QLabel(label), i, 0)
            travel_grid.addWidget(spin, i, 1)
            ws[attr] = spin

        layout.addWidget(travel_group)

        # Homing
        home_group = QGroupBox("Homing Parameters")
        home_grid = QGridLayout(home_group)
        home_grid.setHorizontalSpacing(16)
        home_grid.setVerticalSpacing(10)

        for i, (label, attr, mn, mx, suffix) in enumerate([
            ("Search Velocity:", "search_velocity", -1000, 1000, "mm/s"),
            ("Latch Velocity:",  "latch_velocity",  -100,  100,  "mm/s"),
        ]):
            spin = QDoubleSpinBox()
            spin.setRange(mn, mx)
            spin.setDecimals(4)
            spin.setValue(getattr(ax, attr))
            spin.setSuffix(f"  {suffix}")
            home_grid.addWidget(QLabel(label), i, 0)
            home_grid.addWidget(spin, i, 1)
            ws[attr] = spin

        seq_spin = QSpinBox()
        seq_spin.setRange(-1, 10)
        seq_spin.setValue(ax.home_sequence)
        home_grid.addWidget(QLabel("Home Sequence:"), 2, 0)
        home_grid.addWidget(seq_spin, 2, 1)
        ws["home_sequence"] = seq_spin

        seq_hint = QLabel("-1 = No homing,  0 = Home simultaneously,  1+ = Home in order")
        seq_hint.setStyleSheet("color: #4C566A; font-size: 8.5pt;")
        home_grid.addWidget(seq_hint, 3, 0, 1, 2)

        layout.addWidget(home_group)
        layout.addStretch()

        self._axis_widgets[letter] = ws
        return widget

    def populate(self, cfg: MachineConfig):
        self._tabs.clear()
        self._axis_widgets.clear()
        for letter in cfg.axis_config:
            ax = cfg.axes.get(letter, AxisConfig(name=letter))
            tab = self._build_axis_tab(letter, ax)
            self._tabs.addTab(tab, f"{letter} Axis")

    def save(self, cfg: MachineConfig):
        for letter, ws in self._axis_widgets.items():
            ax = cfg.axes.get(letter)
            if not ax:
                continue
            for attr, widget in ws.items():
                if isinstance(widget, QDoubleSpinBox):
                    setattr(ax, attr, widget.value())
                elif isinstance(widget, QSpinBox):
                    setattr(ax, attr, widget.value())


# ─────────────────────────────────────────────────────────────────────────────
# Spindle Configuration Page
# ─────────────────────────────────────────────────────────────────────────────

class SpindleConfigPage(BasePage):
    PAGE_TITLE = "Spindle Configuration"
    PAGE_SUBTITLE = "Configure spindle speed, encoder, and analog output parameters"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 24, 32, 24)
        root.setSpacing(16)

        # ── Analog Output ─────────────────────────────────────────────────────
        analog_group = QGroupBox("Analog Spindle Output")
        analog_grid = QGridLayout(analog_group)
        analog_grid.setHorizontalSpacing(16)
        analog_grid.setVerticalSpacing(10)

        self._max_voltage = QDoubleSpinBox()
        self._max_voltage.setRange(0, 15)
        self._max_voltage.setValue(10.0)
        self._max_voltage.setSuffix(" V")
        analog_grid.addWidget(QLabel("Analog Max Voltage:"), 0, 0)
        analog_grid.addWidget(self._max_voltage, 0, 1)

        self._min_rpm = QDoubleSpinBox()
        self._min_rpm.setRange(0, 100000)
        self._min_rpm.setValue(0)
        self._min_rpm.setSuffix(" RPM")
        analog_grid.addWidget(QLabel("Min RPM:"), 1, 0)
        analog_grid.addWidget(self._min_rpm, 1, 1)

        self._max_rpm = QDoubleSpinBox()
        self._max_rpm.setRange(1, 100000)
        self._max_rpm.setValue(3000)
        self._max_rpm.setSuffix(" RPM")
        analog_grid.addWidget(QLabel("Max RPM:"), 2, 0)
        analog_grid.addWidget(self._max_rpm, 2, 1)

        self._acceleration = QDoubleSpinBox()
        self._acceleration.setRange(1, 100000)
        self._acceleration.setValue(200)
        self._acceleration.setSuffix(" RPM/s")
        analog_grid.addWidget(QLabel("Acceleration:"), 3, 0)
        analog_grid.addWidget(self._acceleration, 3, 1)

        root.addWidget(analog_group)

        # ── Encoder ───────────────────────────────────────────────────────────
        enc_group = QGroupBox("Spindle Encoder")
        enc_grid = QGridLayout(enc_group)
        enc_grid.setHorizontalSpacing(16)
        enc_grid.setVerticalSpacing(10)

        self._use_encoder = QCheckBox("Use spindle encoder for speed feedback")
        enc_grid.addWidget(self._use_encoder, 0, 0, 1, 2)

        self._encoder_scale = QDoubleSpinBox()
        self._encoder_scale.setRange(1, 100000)
        self._encoder_scale.setValue(100)
        self._encoder_scale.setSuffix(" counts/rev")
        enc_grid.addWidget(QLabel("Encoder Scale:"), 1, 0)
        enc_grid.addWidget(self._encoder_scale, 1, 1)

        self._spindle_at_speed = QCheckBox("Wait for spindle at speed")
        enc_grid.addWidget(self._spindle_at_speed, 2, 0, 1, 2)

        root.addWidget(enc_group)
        root.addStretch()

    def populate(self, cfg: MachineConfig):
        sp = cfg.spindle
        self._max_voltage.setValue(sp.analog_max_voltage)
        self._min_rpm.setValue(sp.min_rpm)
        self._max_rpm.setValue(sp.max_rpm)
        self._acceleration.setValue(sp.acceleration)
        self._use_encoder.setChecked(sp.use_encoder)
        self._encoder_scale.setValue(sp.encoder_scale)
        self._spindle_at_speed.setChecked(sp.spindle_at_speed)

    def save(self, cfg: MachineConfig):
        sp = cfg.spindle
        sp.analog_max_voltage = self._max_voltage.value()
        sp.min_rpm = self._min_rpm.value()
        sp.max_rpm = self._max_rpm.value()
        sp.acceleration = self._acceleration.value()
        sp.use_encoder = self._use_encoder.isChecked()
        sp.encoder_scale = self._encoder_scale.value()
        sp.spindle_at_speed = self._spindle_at_speed.isChecked()


# ─────────────────────────────────────────────────────────────────────────────
# Options Page
# ─────────────────────────────────────────────────────────────────────────────

class OptionsPage(BasePage):
    PAGE_TITLE = "Options"
    PAGE_SUBTITLE = "HALUI commands, ClassicLadder PLC, and custom programs"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 24, 32, 24)
        root.setSpacing(16)

        # ── HALUI ─────────────────────────────────────────────────────────────
        halui_group = QGroupBox("HALUI MDI Commands")
        halui_layout = QVBoxLayout(halui_group)

        info = QLabel("Add MDI G-code commands accessible via HALUI pins.")
        info.setStyleSheet("color: #81A1C1; font-size: 9pt;")
        halui_layout.addWidget(info)

        self._halui_list = QListWidget()
        halui_layout.addWidget(self._halui_list)

        btn_row = QHBoxLayout()
        self._halui_cmd_input = QLineEdit()
        self._halui_cmd_input.setPlaceholderText("G0 Z10 (MDI command)")
        add_btn = QPushButton("Add")
        remove_btn = QPushButton("Remove")
        add_btn.clicked.connect(self._add_halui_cmd)
        remove_btn.clicked.connect(self._remove_halui_cmd)
        btn_row.addWidget(self._halui_cmd_input)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(remove_btn)
        halui_layout.addLayout(btn_row)

        root.addWidget(halui_group)

        # ── ClassicLadder ─────────────────────────────────────────────────────
        cl_group = QGroupBox("ClassicLadder PLC")
        cl_layout = QGridLayout(cl_group)
        cl_layout.setHorizontalSpacing(16)
        cl_layout.setVerticalSpacing(10)

        self._use_classicladder = QCheckBox("Include ClassicLadder PLC")
        cl_layout.addWidget(self._use_classicladder, 0, 0, 1, 2)

        self._cl_program = QLineEdit()
        self._cl_program.setPlaceholderText("my_ladder.clp")
        cl_browse = QPushButton("Browse…")
        cl_browse.setFixedWidth(90)
        cl_layout.addWidget(QLabel("Ladder Program:"), 1, 0)
        cl_layout.addWidget(self._cl_program, 1, 1)
        cl_layout.addWidget(cl_browse, 1, 2)

        self._use_classicladder.toggled.connect(self._cl_program.setEnabled)
        self._cl_program.setEnabled(False)

        root.addWidget(cl_group)

        # ── Custom HAL ────────────────────────────────────────────────────────
        hal_group = QGroupBox("Custom HAL Snippets")
        hal_layout = QVBoxLayout(hal_group)

        hal_layout.addWidget(QLabel("Custom HAL (inserted before main nets):"))
        self._custom_hal_before = QTextEdit()
        self._custom_hal_before.setMaximumHeight(80)
        self._custom_hal_before.setPlaceholderText("# HAL commands...")
        hal_layout.addWidget(self._custom_hal_before)

        hal_layout.addWidget(QLabel("Custom HAL (inserted after main nets):"))
        self._custom_hal_after = QTextEdit()
        self._custom_hal_after.setMaximumHeight(80)
        self._custom_hal_after.setPlaceholderText("# HAL commands...")
        hal_layout.addWidget(self._custom_hal_after)

        root.addWidget(hal_group)
        root.addStretch()

    def _add_halui_cmd(self):
        cmd = self._halui_cmd_input.text().strip()
        if cmd:
            self._halui_list.addItem(cmd)
            self._halui_cmd_input.clear()

    def _remove_halui_cmd(self):
        row = self._halui_list.currentRow()
        if row >= 0:
            self._halui_list.takeItem(row)

    def populate(self, cfg: MachineConfig):
        o = cfg.options
        self._halui_list.clear()
        for cmd in o.halui_commands:
            self._halui_list.addItem(cmd)
        self._use_classicladder.setChecked(o.use_classicladder)
        self._cl_program.setText(o.classicladder_program)
        self._custom_hal_before.setPlainText(o.custom_hal_before)
        self._custom_hal_after.setPlainText(o.custom_hal_after)

    def save(self, cfg: MachineConfig):
        o = cfg.options
        o.halui_commands = [
            self._halui_list.item(i).text()
            for i in range(self._halui_list.count())
        ]
        o.num_halui_commands = len(o.halui_commands)
        o.use_classicladder = self._use_classicladder.isChecked()
        o.classicladder_program = self._cl_program.text()
        o.custom_hal_before = self._custom_hal_before.toPlainText()
        o.custom_hal_after = self._custom_hal_after.toPlainText()


# ─────────────────────────────────────────────────────────────────────────────
# Realtime Components Page
# ─────────────────────────────────────────────────────────────────────────────

class RealtimePage(BasePage):
    PAGE_TITLE = "Realtime Components"
    PAGE_SUBTITLE = "Select additional HAL real-time kernel modules to load"

    STANDARD_COMPONENTS = [
        ("absolute",  "Compute absolute value of a signal"),
        ("pid",       "PID controller (usually required for servo)"),
        ("scale",     "Scale a signal by a constant factor"),
        ("mux2",      "Two-input multiplexer (select between signals)"),
        ("lowpass",   "Low-pass filter for noisy signals"),
        ("estop_latch","Latching E-stop logic"),
        ("logic",     "Combinational logic gates"),
        ("oneshot",   "One-shot pulse generator"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._checkboxes: dict[str, QCheckBox] = {}
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 24, 32, 24)
        root.setSpacing(16)

        std_group = QGroupBox("Standard HAL Components")
        std_layout = QVBoxLayout(std_group)

        for name, desc in self.STANDARD_COMPONENTS:
            cb = QCheckBox(f"{name}  —  {desc}")
            self._checkboxes[name] = cb
            std_layout.addWidget(cb)

        root.addWidget(std_group)

        # Custom
        custom_group = QGroupBox("Custom HAL Components")
        custom_layout = QVBoxLayout(custom_group)
        custom_layout.addWidget(QLabel("One component per line (e.g.  comp_name  or  comp_name count=2):"))
        self._custom_text = QTextEdit()
        self._custom_text.setMaximumHeight(100)
        self._custom_text.setPlaceholderText("# custom_component\n# my_filter count=2")
        custom_layout.addWidget(self._custom_text)
        root.addWidget(custom_group)
        root.addStretch()

    def populate(self, cfg: MachineConfig):
        rt = cfg.realtime
        attr_map = {
            "absolute": "use_absolute",
            "pid":      "use_pid",
            "scale":    "use_scale",
            "mux2":     "use_mux2",
            "lowpass":  "use_lowpass",
        }
        for name, cb in self._checkboxes.items():
            attr = attr_map.get(name)
            if attr:
                cb.setChecked(getattr(rt, attr, False))

        self._custom_text.setPlainText("\n".join(rt.custom_components))

    def save(self, cfg: MachineConfig):
        rt = cfg.realtime
        rt.use_absolute = self._checkboxes.get("absolute", QCheckBox()).isChecked()
        rt.use_pid      = self._checkboxes.get("pid",      QCheckBox()).isChecked()
        rt.use_scale    = self._checkboxes.get("scale",    QCheckBox()).isChecked()
        rt.use_mux2     = self._checkboxes.get("mux2",     QCheckBox()).isChecked()
        rt.use_lowpass  = self._checkboxes.get("lowpass",  QCheckBox()).isChecked()
        rt.custom_components = [
            line.strip()
            for line in self._custom_text.toPlainText().splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
