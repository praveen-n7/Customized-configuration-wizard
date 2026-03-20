"""
7i76 I/O Configuration Page
Motor Configuration Page
Axis Scale Calculation Page
"""
from __future__ import annotations

try:
    from PyQt6.QtWidgets import (
        QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
        QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox,
        QGroupBox, QCheckBox, QTabWidget, QTableWidget,
        QTableWidgetItem, QHeaderView, QWidget, QPushButton,
    )
    from PyQt6.QtCore import Qt
except ImportError:
    from PySide6.QtWidgets import (
        QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
        QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox,
        QGroupBox, QCheckBox, QTabWidget, QTableWidget,
        QTableWidgetItem, QHeaderView, QWidget, QPushButton,
    )
    from PySide6.QtCore import Qt

from pages.base_page import BasePage
from config.machine_config import MachineConfig, AxisConfig


# ─────────────────────────────────────────────────────────────────────────────
# 7i76 I/O Page
# ─────────────────────────────────────────────────────────────────────────────

INPUT_FUNCTIONS = [
    "Unused", "E-Stop", "Home X", "Home Y", "Home Z", "Home A",
    "Limit X+", "Limit X-", "Limit Z+", "Limit Z-", "Limit Y+", "Limit Y-",
    "Probe", "Spindle Index", "Amp Fault X", "Amp Fault Z",
    "Custom MDI", "Coolant Override", "Feed Override",
]


class IO7i76Page(BasePage):
    PAGE_TITLE = "7i76 I/O Configuration"
    PAGE_SUBTITLE = "Assign functions to 7i76 terminal block inputs and analog outputs"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 16, 24, 16)
        root.setSpacing(12)

        self._tabs = QTabWidget()
        root.addWidget(self._tabs)

        # TB6 – 16 digital inputs
        self._tb6_table = self._make_input_table(16, "TB6")
        self._tabs.addTab(self._tb6_table, "TB6 Inputs (Digital)")

        # TB5 – 16 digital inputs
        self._tb5_table = self._make_input_table(16, "TB5")
        self._tabs.addTab(self._tb5_table, "TB5 Inputs (Digital)")

        # TB4 – Analog outputs
        self._tb4_table = self._make_analog_table()
        self._tabs.addTab(self._tb4_table, "TB4 Analog Outputs")

    def _make_input_table(self, num_pins: int, prefix: str) -> QTableWidget:
        table = QTableWidget(num_pins, 3)
        table.setHorizontalHeaderLabels(["Pin", "Function", "Invert"])
        hdr = table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        table.setColumnWidth(0, 60)
        table.setColumnWidth(2, 70)
        table.verticalHeader().setVisible(False)
        table.setAlternatingRowColors(True)

        for row in range(num_pins):
            pin_item = QTableWidgetItem(f"{prefix}-{row + 1}")
            pin_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            pin_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(row, 0, pin_item)

            func_combo = QComboBox()
            func_combo.addItems(INPUT_FUNCTIONS)
            table.setCellWidget(row, 1, func_combo)

            cb_widget = QWidget()
            cb_layout = QHBoxLayout(cb_widget)
            cb_layout.setContentsMargins(0, 0, 0, 0)
            cb_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cb_layout.addWidget(QCheckBox())
            table.setCellWidget(row, 2, cb_widget)

            table.setRowHeight(row, 30)

        return table

    def _make_analog_table(self) -> QTableWidget:
        num = 2  # 7i76 has 2 analog outputs
        table = QTableWidget(num, 4)
        table.setHorizontalHeaderLabels(["Channel", "Function", "Min V", "Max V"])
        hdr = table.horizontalHeader()
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        table.setColumnWidth(0, 70)
        table.setColumnWidth(2, 70)
        table.setColumnWidth(3, 70)
        table.verticalHeader().setVisible(False)
        table.setAlternatingRowColors(True)

        funcs = ["Spindle Speed", "Unused"]
        for row in range(num):
            ch_item = QTableWidgetItem(f"AOut-{row + 1}")
            ch_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            table.setItem(row, 0, ch_item)

            func_combo = QComboBox()
            func_combo.addItems(funcs)
            if row < len(funcs):
                func_combo.setCurrentIndex(row)
            table.setCellWidget(row, 1, func_combo)

            for col, val in [(2, "0.0"), (3, "10.0")]:
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(row, col, item)

            table.setRowHeight(row, 30)

        return table

    def populate(self, cfg: MachineConfig):
        pass  # TODO: restore from cfg.io

    def save(self, cfg: MachineConfig):
        pass  # TODO: save to cfg.io


# ─────────────────────────────────────────────────────────────────────────────
# Motor Configuration Page
# ─────────────────────────────────────────────────────────────────────────────

class MotorConfigPage(BasePage):
    PAGE_TITLE = "Motor Configuration"
    PAGE_SUBTITLE = "Set PID, stepper timing, and motion limits per axis motor"

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

        # ── PID ──────────────────────────────────────────────────────────────
        pid_group = QGroupBox("PID Parameters")
        pid_grid = QGridLayout(pid_group)
        pid_grid.setHorizontalSpacing(16)
        pid_grid.setVerticalSpacing(8)

        for i, (label, attr, rng) in enumerate([
            ("P Gain", "pid_p", (0, 10000)),
            ("I Gain", "pid_i", (0, 10000)),
            ("D Gain", "pid_d", (0, 10000)),
            ("FF0",    "pid_ff0", (-1000, 1000)),
            ("FF1",    "pid_ff1", (-1000, 1000)),
            ("FF2",    "pid_ff2", (-1000, 1000)),
            ("Bias",   "pid_bias", (-10, 10)),
            ("Max Output", "pid_max_output", (0, 100)),
        ]):
            row, col = divmod(i, 2)
            spin = QDoubleSpinBox()
            spin.setRange(*rng)
            spin.setDecimals(4)
            spin.setValue(getattr(ax, attr))
            spin.setDecimals(3)
            pid_grid.addWidget(QLabel(f"{label}:"), row, col * 2)
            pid_grid.addWidget(spin, row, col * 2 + 1)
            ws[attr] = spin

        layout.addWidget(pid_group)

        # ── Stepper Timing ────────────────────────────────────────────────────
        step_group = QGroupBox("Stepper Timing (nanoseconds)")
        step_grid = QGridLayout(step_group)
        step_grid.setHorizontalSpacing(16)
        step_grid.setVerticalSpacing(8)

        for i, (label, attr) in enumerate([
            ("Step Time",       "step_time"),
            ("Step Space",      "step_space"),
            ("Direction Hold",  "direction_hold"),
            ("Direction Setup", "direction_setup"),
        ]):
            spin = QSpinBox()
            spin.setRange(0, 1_000_000)
            spin.setSingleStep(1000)
            spin.setValue(getattr(ax, attr))
            spin.setSuffix(" ns")
            step_grid.addWidget(QLabel(f"{label}:"), i, 0)
            step_grid.addWidget(spin, i, 1)
            ws[attr] = spin

        layout.addWidget(step_group)

        # ── Motion Limits ─────────────────────────────────────────────────────
        motion_group = QGroupBox("Motion Limits")
        motion_grid = QGridLayout(motion_group)
        motion_grid.setHorizontalSpacing(16)
        motion_grid.setVerticalSpacing(8)

        for i, (label, attr, unit) in enumerate([
            ("Max Velocity",     "max_velocity",     "mm/s"),
            ("Max Acceleration", "max_acceleration",  "mm/s²"),
            ("Following Error",  "ferror",            "mm"),
            ("Min Following Error", "min_ferror",     "mm"),
        ]):
            spin = QDoubleSpinBox()
            spin.setRange(0.001, 100000)
            spin.setValue(getattr(ax, attr))
            spin.setSuffix(f"  {unit}")
            motion_grid.addWidget(QLabel(f"{label}:"), i, 0)
            motion_grid.addWidget(spin, i, 1)
            ws[attr] = spin

        layout.addWidget(motion_group)
        layout.addStretch()

        self._axis_widgets[letter] = ws
        return widget

    def populate(self, cfg: MachineConfig):
        self._tabs.clear()
        self._axis_widgets.clear()
        for letter in cfg.axis_config:
            ax = cfg.axes.get(letter, AxisConfig(name=letter))
            tab = self._build_axis_tab(letter, ax)
            self._tabs.addTab(tab, f"{letter} Motor")

    def save(self, cfg: MachineConfig):
        for letter, ws in self._axis_widgets.items():
            ax = cfg.axes.get(letter)
            if ax is None:
                continue
            for attr, widget in ws.items():
                if isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                    setattr(ax, attr, widget.value())


# ─────────────────────────────────────────────────────────────────────────────
# Axis Scale Calculation Page
# ─────────────────────────────────────────────────────────────────────────────

class AxisScalePage(BasePage):
    PAGE_TITLE = "Axis Scale Calculation"
    PAGE_SUBTITLE = "Calculate steps/mm from mechanical drive train parameters"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._axis_widgets: dict[str, dict] = {}
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 16, 24, 16)
        root.setSpacing(12)

        info = QLabel(
            "Scale = (Motor Steps/Rev × Microstep) / (Leadscrew Pitch × Pulley Ratio × Worm Ratio)"
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #81A1C1; font-size: 9.5pt; font-family: monospace;")
        root.addWidget(info)

        self._tabs = QTabWidget()
        root.addWidget(self._tabs)

    def _build_axis_tab(self, letter: str, ax: AxisConfig) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(14)
        ws: dict = {}

        group = QGroupBox(f"{letter} Axis Drive Train")
        grid = QGridLayout(group)
        grid.setHorizontalSpacing(20)
        grid.setVerticalSpacing(10)

        fields = [
            ("Motor Steps/Revolution:", "motor_steps_rev", QSpinBox, 1, 10000, 1, ""),
            ("Microstep Multiplier:",   "microstep",       QSpinBox, 1, 256,   1, "×"),
            ("Pulley Ratio:",           "pulley_ratio",    QDoubleSpinBox, 0.01, 100, 0.1, ":1"),
            ("Worm Gear Ratio:",        "worm_ratio",      QDoubleSpinBox, 0.01, 1000, 1, ":1"),
            ("Leadscrew Pitch:",        "leadscrew_pitch", QDoubleSpinBox, 0.001, 100, 0.5, "mm/rev"),
        ]

        for i, (label, attr, cls, mn, mx, step, suffix) in enumerate(fields):
            if cls is QSpinBox:
                spin = QSpinBox()
                spin.setRange(mn, mx)
                spin.setValue(int(getattr(ax, attr)))
            else:
                spin = QDoubleSpinBox()
                spin.setRange(mn, mx)
                spin.setSingleStep(step)
                spin.setDecimals(4)
                spin.setValue(float(getattr(ax, attr)))
            if suffix:
                spin.setSuffix(f"  {suffix}")
            grid.addWidget(QLabel(label), i, 0)
            grid.addWidget(spin, i, 1)
            ws[attr] = spin
            spin.valueChanged.connect(lambda _, l=letter: self._recalculate(l))

        layout.addWidget(group)

        # Result display
        result_frame = QGroupBox("Calculated Scale")
        result_layout = QHBoxLayout(result_frame)
        ws["_result_label"] = QLabel("—")
        ws["_result_label"].setStyleSheet(
            "color: #A3BE8C; font-size: 14pt; font-weight: 700; font-family: monospace;"
        )
        ws["_result_label"].setAlignment(Qt.AlignmentFlag.AlignCenter)
        result_layout.addWidget(ws["_result_label"])
        layout.addWidget(result_frame)

        # Encoder lines
        enc_group = QGroupBox("Encoder (if servo)")
        enc_grid = QGridLayout(enc_group)
        enc_spin = QSpinBox()
        enc_spin.setRange(100, 100000)
        enc_spin.setSingleStep(100)
        enc_spin.setValue(ax.encoder_lines)
        enc_spin.setSuffix(" lines/rev")
        enc_grid.addWidget(QLabel("Encoder Lines:"), 0, 0)
        enc_grid.addWidget(enc_spin, 0, 1)
        ws["encoder_lines"] = enc_spin
        layout.addWidget(enc_group)

        layout.addStretch()
        self._axis_widgets[letter] = ws
        return widget

    def _recalculate(self, letter: str):
        ws = self._axis_widgets.get(letter)
        if not ws:
            return
        try:
            steps = ws["motor_steps_rev"].value()
            micro = ws["microstep"].value()
            pitch = ws["leadscrew_pitch"].value()
            pulley = ws["pulley_ratio"].value()
            worm = ws["worm_ratio"].value()
            if pitch * pulley * worm == 0:
                ws["_result_label"].setText("÷0 error")
                return
            scale = (steps * micro) / (pitch * pulley * worm)
            ws["_result_label"].setText(f"{scale:.4f} steps/mm")
        except Exception:
            ws["_result_label"].setText("error")

    def populate(self, cfg: MachineConfig):
        self._tabs.clear()
        self._axis_widgets.clear()
        for letter in cfg.axis_config:
            ax = cfg.axes.get(letter, AxisConfig(name=letter))
            tab = self._build_axis_tab(letter, ax)
            self._tabs.addTab(tab, f"{letter} Scale")
            self._recalculate(letter)

    def save(self, cfg: MachineConfig):
        for letter, ws in self._axis_widgets.items():
            ax = cfg.axes.get(letter)
            if not ax:
                continue
            for attr in ["motor_steps_rev", "microstep", "encoder_lines"]:
                if attr in ws:
                    setattr(ax, attr, ws[attr].value())
            for attr in ["pulley_ratio", "worm_ratio", "leadscrew_pitch"]:
                if attr in ws:
                    setattr(ax, attr, ws[attr].value())
            # Recalculate and store scale
            try:
                steps = ax.motor_steps_rev
                micro = ax.microstep
                pitch = ax.leadscrew_pitch
                pulley = ax.pulley_ratio
                worm = ax.worm_ratio
                if pitch * pulley * worm != 0:
                    ax.scale = (steps * micro) / (pitch * pulley * worm)
            except Exception:
                pass
