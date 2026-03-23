"""
Full-Parity Motor & Axis Configuration Pages
=============================================
Exact replication of ALL LinuxCNC PnCconf "Axis Configuration" and
"Motor Configuration" wizard parameters, including:
  - Travel & Limits
  - Homing Configuration (full)
  - Motor Type (Stepper / Servo) with dynamic show/hide
  - Stepper Timing (nanoseconds)
  - Servo PID Parameters
  - Scaling (Encoder + Stepper) with Calculate Scale popup
  - Motion Limits
  - Backlash & Compensation file
  - Per-axis: X, Y, Z via QTabWidget

Compatible with PyQt6 and PySide6.
"""

from __future__ import annotations

import math
from typing import Dict, Optional

try:
    from PyQt6.QtWidgets import (
        QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
        QLabel, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox,
        QGroupBox, QCheckBox, QTabWidget, QWidget, QPushButton,
        QDialog, QFileDialog, QScrollArea, QFrame, QSizePolicy,
        QTableWidget, QTableWidgetItem, QHeaderView,
    )
    from PyQt6.QtCore import Qt, pyqtSignal as Signal
except ImportError:
    from PySide6.QtWidgets import (
        QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
        QLabel, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox,
        QGroupBox, QCheckBox, QTabWidget, QWidget, QPushButton,
        QDialog, QFileDialog, QScrollArea, QFrame, QSizePolicy,
        QTableWidget, QTableWidgetItem, QHeaderView,
    )
    from PySide6.QtCore import Qt, Signal

from pages.base_page import BasePage
from config.machine_config import MachineConfig, AxisConfig


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DRIVER_TYPES = [
    "Custom", "TB6600", "DM542", "DM860", "MA860H", "HobbyCNC", "Keling",
    "Gecko201", "Gecko202", "Gecko203v", "Gecko210", "Gecko212",
    "Gecko320", "Gecko540", "L297", "PMDX-150", "Pololu",
    "SolarBotics", "Xylotex",
]

HOME_SEARCH_SEQUENCES = [
    "0 – No homing",
    "1 – First joint homes first",
    "2 – Second joint homes first",
    "3 – Third joint homes first",
    "-1 – Shared switch (neg)",
    "-2 – Shared switch (neg 2nd)",
    "-3 – Shared switch (neg 3rd)",
]

COMPENSATION_TYPES = ["Type 1", "Type 2", "Type 3"]

UNIT_LABELS = {
    "metric": {"vel": "mm/s", "acc": "mm/s²", "dist": "mm"},
    "inch":   {"vel": "in/s", "acc": "in/s²", "dist": "in"},
}

INPUT_FUNCTIONS = [
    "Unused", "E-Stop", "Home X", "Home Y", "Home Z", "Home A",
    "Limit X+", "Limit X-", "Limit Z+", "Limit Z-", "Limit Y+", "Limit Y-",
    "Probe", "Spindle Index", "Amp Fault X", "Amp Fault Z",
    "Custom MDI", "Coolant Override", "Feed Override",
]


# ---------------------------------------------------------------------------
# Widget Factories
# ---------------------------------------------------------------------------

def _dspin(value, lo, hi, decimals=4, step=0.1, suffix=""):
    s = QDoubleSpinBox()
    s.setRange(lo, hi)
    s.setDecimals(decimals)
    s.setSingleStep(step)
    s.setValue(value)
    if suffix:
        s.setSuffix("  " + suffix)
    s.setMinimumWidth(110)
    return s


def _ispin(value, lo, hi, step=1, suffix=""):
    s = QSpinBox()
    s.setRange(lo, hi)
    s.setSingleStep(step)
    s.setValue(value)
    if suffix:
        s.setSuffix("  " + suffix)
    s.setMinimumWidth(110)
    return s


# ---------------------------------------------------------------------------
# Axis Scale Calculation Dialog
# ---------------------------------------------------------------------------

class AxisScaleDialog(QDialog):
    """
    Full replication of LinuxCNC PnCconf 'Axis Scale Calculation' popup.
    """

    scale_applied = Signal(float, float)   # (stepper_scale, encoder_scale)

    def __init__(self, axis_letter, units="metric", ax=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Axis Scale Calculation")
        self.setMinimumWidth(560)
        self.setModal(True)
        self._units = units
        self._ax = ax or AxisConfig(name=axis_letter)
        self._letter = axis_letter
        self._max_vel = 50.0
        self._max_accel = 500.0
        self._build_ui()
        self._recalculate()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(12)

        pitch_unit = "mm / rev" if self._units == "metric" else "in / rev"

        # ── Step Motor Scale ─────────────────────────────────────────────────
        sm_group = QGroupBox("Step Motor Scale")
        sm_form = QFormLayout(sm_group)
        sm_form.setHorizontalSpacing(16)
        sm_form.setVerticalSpacing(8)
        sm_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._cb_pulley = QCheckBox()
        self._pulley_motor = _ispin(1, 1, 500)
        self._pulley_ls = _ispin(1, 1, 500)
        pulley_row = QHBoxLayout()
        pulley_row.addWidget(self._cb_pulley)
        pulley_row.addWidget(self._pulley_motor)
        pulley_row.addWidget(QLabel(":"))
        pulley_row.addWidget(self._pulley_ls)
        pulley_row.addStretch()
        sm_form.addRow("Pulley teeth (motor:Leadscrew):", pulley_row)

        self._cb_worm = QCheckBox()
        self._worm_in = _ispin(1, 1, 9999)
        self._worm_out = _ispin(1, 1, 9999)
        worm_row = QHBoxLayout()
        worm_row.addWidget(self._cb_worm)
        worm_row.addWidget(self._worm_in)
        worm_row.addWidget(QLabel(":"))
        worm_row.addWidget(self._worm_out)
        worm_row.addStretch()
        sm_form.addRow("Worm turn ratio (Input:Output):", worm_row)

        self._cb_micro = QCheckBox()
        self._micro_spin = _ispin(self._ax.microstep, 1, 256)
        micro_row = QHBoxLayout()
        micro_row.addWidget(self._cb_micro)
        micro_row.addWidget(self._micro_spin)
        micro_row.addStretch()
        sm_form.addRow("Microstep Multiplication Factor:", micro_row)

        self._cb_ls_metric = QCheckBox()
        self._ls_metric = _dspin(self._ax.leadscrew_pitch, 0.001, 100, 4, 0.5)
        ls_m_row = QHBoxLayout()
        ls_m_row.addWidget(self._cb_ls_metric)
        ls_m_row.addWidget(self._ls_metric)
        ls_m_row.addWidget(QLabel(pitch_unit))
        ls_m_row.addStretch()
        sm_form.addRow("Leadscrew Metric Pitch:", ls_m_row)

        self._cb_ls_tpi = QCheckBox()
        self._ls_tpi = _dspin(5.0, 0.5, 200, 4, 0.5)
        ls_t_row = QHBoxLayout()
        ls_t_row.addWidget(self._cb_ls_tpi)
        ls_t_row.addWidget(self._ls_tpi)
        ls_t_row.addWidget(QLabel("TPI"))
        ls_t_row.addStretch()
        sm_form.addRow("Leadscrew TPI:", ls_t_row)

        self._motor_steps = _ispin(self._ax.motor_steps_rev, 1, 10000, 1)
        sm_form.addRow("Motor steps per revolution:", self._motor_steps)
        root.addWidget(sm_group)

        # ── Encoder Scale ────────────────────────────────────────────────────
        enc_group = QGroupBox("Encoder Scale")
        enc_form = QFormLayout(enc_group)
        enc_form.setHorizontalSpacing(16)
        enc_form.setVerticalSpacing(8)
        enc_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._cb_enc_pulley = QCheckBox()
        self._enc_pulley_m = _ispin(1, 1, 500)
        self._enc_pulley_ls = _ispin(1, 1, 500)
        ep_row = QHBoxLayout()
        ep_row.addWidget(self._cb_enc_pulley)
        ep_row.addWidget(self._enc_pulley_m)
        ep_row.addWidget(QLabel(":"))
        ep_row.addWidget(self._enc_pulley_ls)
        ep_row.addStretch()
        enc_form.addRow("Pulley teeth (encoder:Leadscrew):", ep_row)

        self._cb_enc_worm = QCheckBox()
        self._enc_worm_in = _ispin(1, 1, 9999)
        self._enc_worm_out = _ispin(1, 1, 9999)
        ew_row = QHBoxLayout()
        ew_row.addWidget(self._cb_enc_worm)
        ew_row.addWidget(self._enc_worm_in)
        ew_row.addWidget(QLabel(":"))
        ew_row.addWidget(self._enc_worm_out)
        ew_row.addStretch()
        enc_form.addRow("Worm turn ratio (Input:Output):", ew_row)

        self._cb_enc_ls = QCheckBox()
        self._enc_ls_metric = _dspin(self._ax.leadscrew_pitch, 0.001, 100, 4, 0.5)
        enc_ls_row = QHBoxLayout()
        enc_ls_row.addWidget(self._cb_enc_ls)
        enc_ls_row.addWidget(self._enc_ls_metric)
        enc_ls_row.addWidget(QLabel(pitch_unit))
        enc_ls_row.addStretch()
        enc_form.addRow("Leadscrew Metric Pitch:", enc_ls_row)

        self._cb_enc_tpi = QCheckBox()
        self._enc_tpi = _dspin(5.0, 0.5, 200, 4, 0.5)
        enc_tpi_row = QHBoxLayout()
        enc_tpi_row.addWidget(self._cb_enc_tpi)
        enc_tpi_row.addWidget(self._enc_tpi)
        enc_tpi_row.addWidget(QLabel("TPI"))
        enc_tpi_row.addStretch()
        enc_form.addRow("Leadscrew TPI:", enc_tpi_row)

        self._enc_lines = _ispin(self._ax.encoder_lines, 100, 100000, 100)
        enc_x4 = QLabel("X 4 = Pulses/Rev")
        enc_x4.setStyleSheet("color:#81A1C1; font-size:8.5pt;")
        enc_lines_row = QHBoxLayout()
        enc_lines_row.addWidget(self._enc_lines)
        enc_lines_row.addWidget(enc_x4)
        enc_lines_row.addStretch()
        enc_form.addRow("Encoder lines per revolution:", enc_lines_row)
        root.addWidget(enc_group)

        # ── Calculated Scale ─────────────────────────────────────────────────
        calc_group = QGroupBox("Calculated Scale")
        calc_form = QFormLayout(calc_group)
        calc_form.setHorizontalSpacing(16)
        calc_form.setVerticalSpacing(6)
        mono = "color:#A3BE8C; font-family:monospace; font-weight:600;"
        self._lbl_motor_steps_unit = QLabel("—")
        self._lbl_motor_steps_unit.setStyleSheet(mono)
        self._lbl_enc_pulses_unit = QLabel("—")
        self._lbl_enc_pulses_unit.setStyleSheet(mono)
        calc_form.addRow("motor steps per unit:", self._lbl_motor_steps_unit)
        calc_form.addRow("encoder pulses per unit:", self._lbl_enc_pulses_unit)
        root.addWidget(calc_group)

        # ── Motion Data ───────────────────────────────────────────────────────
        motion_group = QGroupBox("Motion Data")
        motion_form = QFormLayout(motion_group)
        motion_form.setHorizontalSpacing(16)
        motion_form.setVerticalSpacing(4)
        dm = "color:#81A1C1; font-family:monospace; font-size:8.5pt;"
        self._lbl_axis_scale  = QLabel("—"); self._lbl_axis_scale.setStyleSheet(dm)
        self._lbl_resolution  = QLabel("—"); self._lbl_resolution.setStyleSheet(dm)
        self._lbl_accel_time  = QLabel("—"); self._lbl_accel_time.setStyleSheet(dm)
        self._lbl_accel_dist  = QLabel("—"); self._lbl_accel_dist.setStyleSheet(dm)
        self._lbl_pulse_rate  = QLabel("—"); self._lbl_pulse_rate.setStyleSheet(dm)
        self._lbl_motor_rpm   = QLabel("—"); self._lbl_motor_rpm.setStyleSheet(dm)
        motion_form.addRow("Calculated Axis SCALE:", self._lbl_axis_scale)
        motion_form.addRow("Resolution:", self._lbl_resolution)
        motion_form.addRow("Time to accelerate to max speed:", self._lbl_accel_time)
        motion_form.addRow("Distance to achieve max speed:", self._lbl_accel_dist)
        motion_form.addRow("Pulse rate at max speed:", self._lbl_pulse_rate)
        motion_form.addRow("Motor RPM at max speed:", self._lbl_motor_rpm)
        root.addWidget(motion_group)

        # ── Buttons ──────────────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self._btn_cancel = QPushButton("✗  Cancel")
        self._btn_apply  = QPushButton("✔  Apply")
        self._btn_apply.setObjectName("btnNext")
        btn_row.addWidget(self._btn_cancel)
        btn_row.addWidget(self._btn_apply)
        root.addLayout(btn_row)

        # Wire
        for w in (self._pulley_motor, self._pulley_ls, self._worm_in,
                  self._worm_out, self._micro_spin, self._ls_metric,
                  self._ls_tpi, self._motor_steps, self._enc_lines,
                  self._enc_pulley_m, self._enc_pulley_ls,
                  self._enc_worm_in, self._enc_worm_out,
                  self._enc_ls_metric, self._enc_tpi):
            w.valueChanged.connect(self._recalculate)

        self._btn_cancel.clicked.connect(self.reject)
        self._btn_apply.clicked.connect(self._on_apply)

    def _recalculate(self):
        try:
            steps_rev = self._motor_steps.value()
            micro     = self._micro_spin.value()
            pitch     = self._ls_metric.value()
            pm = self._pulley_motor.value(); pl = self._pulley_ls.value()
            pulley_ratio = pm / pl if pl else 1.0
            wi = self._worm_in.value(); wo = self._worm_out.value()
            worm_ratio = wi / wo if wo else 1.0
            denom = pitch * pulley_ratio * worm_ratio
            if denom == 0:
                for lbl in (self._lbl_motor_steps_unit, self._lbl_axis_scale):
                    lbl.setText("÷0 error")
                return

            stepper_scale = (steps_rev * micro) / denom
            u = "mm" if self._units == "metric" else "inch"
            self._lbl_motor_steps_unit.setText(f"{stepper_scale:.4f}")
            self._lbl_axis_scale.setText(f"{stepper_scale:.1f} Steps / {u}")
            res = 1.0 / stepper_scale if stepper_scale else 0
            self._lbl_resolution.setText(f"{res:.7f} {u} / Step")

            # Encoder scale
            enc_lines = self._enc_lines.value()
            epm = self._enc_pulley_m.value(); epl = self._enc_pulley_ls.value()
            enc_pr = epm / epl if epl else 1.0
            ewi = self._enc_worm_in.value(); ewo = self._enc_worm_out.value()
            enc_wr = ewi / ewo if ewo else 1.0
            enc_denom = pitch * enc_pr * enc_wr
            if enc_denom:
                enc_scale = (enc_lines * 4) / enc_denom
                self._lbl_enc_pulses_unit.setText(f"{enc_scale:.4f}")
            else:
                self._lbl_enc_pulses_unit.setText("—")

            # Motion
            if stepper_scale > 0 and self._max_vel > 0:
                pulse_khz   = (stepper_scale * self._max_vel) / 1000.0
                motor_rpm   = (self._max_vel / pitch) * 60.0 if pitch else 0
                accel_time  = self._max_vel / self._max_accel if self._max_accel else 0
                accel_dist  = 0.5 * self._max_vel * accel_time
                self._lbl_accel_time.setText(f"{accel_time:.4f} sec")
                self._lbl_accel_dist.setText(f"{accel_dist:.4f} {u}")
                self._lbl_pulse_rate.setText(f"{pulse_khz:.1f} Khz")
                self._lbl_motor_rpm.setText(f"{motor_rpm:.0f} RPM")
        except Exception as e:
            for lbl in (self._lbl_motor_steps_unit, self._lbl_axis_scale,
                        self._lbl_resolution, self._lbl_pulse_rate):
                lbl.setText(f"Error")

    def set_motion_params(self, max_vel, max_accel):
        self._max_vel = max_vel
        self._max_accel = max_accel
        self._recalculate()

    def _on_apply(self):
        try:
            pm = self._pulley_motor.value(); pl = self._pulley_ls.value()
            pulley = pm / pl if pl else 1.0
            wi = self._worm_in.value(); wo = self._worm_out.value()
            worm = wi / wo if wo else 1.0
            pitch = self._ls_metric.value()
            steps_rev = self._motor_steps.value()
            micro = self._micro_spin.value()
            denom = pitch * pulley * worm
            stepper_scale = (steps_rev * micro) / denom if denom else 0.0

            enc_lines = self._enc_lines.value()
            epm = self._enc_pulley_m.value(); epl = self._enc_pulley_ls.value()
            enc_pr = epm / epl if epl else 1.0
            ewi = self._enc_worm_in.value(); ewo = self._enc_worm_out.value()
            enc_wr = ewi / ewo if ewo else 1.0
            enc_denom = pitch * enc_pr * enc_wr
            enc_scale = (enc_lines * 4) / enc_denom if enc_denom else 0.0

            self.scale_applied.emit(stepper_scale, enc_scale)
            self.accept()
        except Exception:
            self.reject()


# ---------------------------------------------------------------------------
# Single Axis Configuration Widget
# ---------------------------------------------------------------------------

class AxisConfigWidget(QScrollArea):
    """
    Complete per-axis configuration widget matching the original PnCconf
    'Axis Configuration' + 'Motor Configuration' pages combined.
    """

    def __init__(self, letter, ax, units="metric", parent=None):
        super().__init__(parent)
        self.letter = letter
        self._ax = ax
        self._units = units
        self._w: Dict = {}

        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)

        inner = QWidget()
        self._layout = QVBoxLayout(inner)
        self._layout.setContentsMargins(16, 12, 16, 12)
        self._layout.setSpacing(14)
        self.setWidget(inner)

        self._build_travel_limits()
        self._build_homing()
        self._build_motor_config()
        self._build_motion_limits()
        self._build_compensation()

        self._layout.addStretch()
        self._motor_type_combo.currentIndexChanged.connect(self._on_motor_type_changed)
        self._on_motor_type_changed()

    # ── Travel Limits ─────────────────────────────────────────────────────────
    def _build_travel_limits(self):
        g = QGroupBox("Travel Limits")
        f = QFormLayout(g)
        f.setHorizontalSpacing(16); f.setVerticalSpacing(8)
        f.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        ul = UNIT_LABELS[self._units]

        w = _dspin(self._ax.travel, -99999, 99999, 4, 1.0, ul["dist"])
        self._w["positive_travel"] = w
        f.addRow("Positive Travel Distance  (Machine zero Origin to end of + travel):", w)

        w = _dspin(0.0, -99999, 99999, 4, 1.0, ul["dist"])
        self._w["negative_travel"] = w
        f.addRow("Negative Travel Distance  (Machine zero Origin to end of – travel):", w)

        w = _dspin(self._ax.home_position, -99999, 99999, 4, 1.0, ul["dist"])
        self._w["final_home_pos"] = w
        f.addRow("Final Home Position location  (Offset from machine zero Origin):", w)

        self._layout.addWidget(g)

    # ── Homing Configuration ──────────────────────────────────────────────────
    def _build_homing(self):
        g = QGroupBox("Homing Configuration")
        f = QFormLayout(g)
        f.setHorizontalSpacing(16); f.setVerticalSpacing(8)
        f.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        ul = UNIT_LABELS[self._units]

        w = _dspin(self._ax.home_switch_location, -99999, 99999, 4, 0.1, ul["dist"])
        self._w["home_switch_loc"] = w
        f.addRow("Home Switch location  (offset from machine zero Origin):", w)

        w = _dspin(self._ax.search_velocity, 0.001, 10000, 4, 1.0, ul["vel"])
        self._w["home_search_vel"] = w
        f.addRow("Home Search Velocity:", w)

        cb = QComboBox()
        cb.addItems(["Towards Negative Limit", "Towards Positive Limit"])
        self._w["home_search_dir"] = cb
        f.addRow("Home Search Direction:", cb)

        w = _dspin(self._ax.latch_velocity, 0.001, 10000, 4, 0.1, ul["vel"])
        self._w["home_latch_vel"] = w
        f.addRow("Home Latch Velocity:", w)

        cb2 = QComboBox()
        cb2.addItems(["Same", "Opposite"])
        self._w["home_latch_dir"] = cb2
        f.addRow("Home Latch Direction:", cb2)

        w = _dspin(0.0, 0.0, 10000, 4, 0.1, ul["vel"])
        self._w["home_final_vel"] = w
        f.addRow("Home Final Velocity:", w)

        ck = QCheckBox("Use Encoder Index For Home")
        self._w["use_enc_index"] = ck
        f.addRow("", ck)

        cb3 = QComboBox()
        cb3.addItems(HOME_SEARCH_SEQUENCES)
        cb3.setCurrentIndex(min(self._ax.home_sequence, len(HOME_SEARCH_SEQUENCES) - 1))
        self._w["home_seq"] = cb3
        f.addRow("Home Search Sequence:", cb3)

        self._layout.addWidget(g)

    # ── Motor Configuration ───────────────────────────────────────────────────
    def _build_motor_config(self):
        outer = QGroupBox("Motor Configuration")
        outer_layout = QVBoxLayout(outer)
        outer_layout.setSpacing(10)

        # Motor type selector row
        type_row = QHBoxLayout()
        type_row.addWidget(QLabel("Motor Type:"))
        self._motor_type_combo = QComboBox()
        self._motor_type_combo.addItems(["Stepper", "Servo"])
        self._motor_type_combo.setMinimumWidth(140)
        self._w["motor_type"] = self._motor_type_combo
        type_row.addWidget(self._motor_type_combo)
        type_row.addStretch()
        outer_layout.addLayout(type_row)

        # ── PID Parameters — ALWAYS VISIBLE (matches original PnCconf layout) ──
        pid_group = QGroupBox("PID Info")
        pid_grid = QGridLayout(pid_group)
        pid_grid.setHorizontalSpacing(12)
        pid_grid.setVerticalSpacing(6)

        pid_fields = [
            ("P",          "pid_p",          self._ax.pid_p,          0,      100000),
            ("I",          "pid_i",          self._ax.pid_i,          0,      100000),
            ("D",          "pid_d",          self._ax.pid_d,          0,      100000),
            ("FF0",        "pid_ff0",        self._ax.pid_ff0,       -1000,    1000),
            ("FF1",        "pid_ff1",        self._ax.pid_ff1,       -1000,    1000),
            ("FF2",        "pid_ff2",        self._ax.pid_ff2,       -1000,    1000),
            ("Bias",       "pid_bias",       self._ax.pid_bias,      -100,     100),
            ("Deadband",   "pid_deadband",   0.0,                     0,      1000),
            ("Max Output", "pid_max_output", self._ax.pid_max_output, 0,      100000),
        ]
        for i, (label, key, val, lo, hi) in enumerate(pid_fields):
            w = _dspin(val, lo, hi, 4, 0.1)
            self._w[key] = w
            pid_grid.addWidget(QLabel(f"{label}:"), i, 0)
            pid_grid.addWidget(w, i, 1)
            # +/- buttons matching original PnCconf style
            btn_minus = QPushButton("–")
            btn_plus  = QPushButton("+")
            btn_minus.setFixedWidth(24); btn_plus.setFixedWidth(24)
            btn_minus.setFixedHeight(24); btn_plus.setFixedHeight(24)
            btn_minus.setStyleSheet("font-size:10pt; font-weight:700; padding:0;")
            btn_plus.setStyleSheet("font-size:10pt; font-weight:700; padding:0;")
            # Connect +/- to increment/decrement the spinbox
            btn_minus.clicked.connect(lambda _, s=w: s.setValue(s.value() - s.singleStep()))
            btn_plus.clicked.connect(lambda _, s=w: s.setValue(s.value() + s.singleStep()))
            pid_grid.addWidget(btn_minus, i, 2)
            pid_grid.addWidget(btn_plus, i, 3)

        outer_layout.addWidget(pid_group)

        # ── Stepper Info — visible only when Stepper selected ─────────────────
        self._stepper_widget = self._build_stepper_section()
        outer_layout.addWidget(self._stepper_widget)

        # ── Servo extra fields — visible only when Servo selected ─────────────
        self._servo_widget = self._build_servo_extras_section()
        outer_layout.addWidget(self._servo_widget)

        # ── Scaling (common to both) ─────────────────────────────────────────
        outer_layout.addWidget(self._build_scaling_section())

        self._layout.addWidget(outer)

    def _build_stepper_section(self):
        g = QGroupBox("Stepper Timing (nanoseconds)")
        grid = QGridLayout(g)
        grid.setHorizontalSpacing(16); grid.setVerticalSpacing(8)

        for row, (label, key, val) in enumerate([
            ("Step On-Time",    "step_time",       self._ax.step_time),
            ("Step Space",      "step_space",      self._ax.step_space),
            ("Direction Hold",  "direction_hold",  self._ax.direction_hold),
            ("Direction Setup", "direction_setup", self._ax.direction_setup),
        ]):
            w = _ispin(val, 0, 1_000_000, 1000, "ns")
            self._w[key] = w
            grid.addWidget(QLabel(f"{label}:"), row, 0)
            grid.addWidget(w, row, 1)

        # Driver type
        self._driver_combo = QComboBox()
        self._driver_combo.addItems(DRIVER_TYPES)
        self._w["driver_type"] = self._driver_combo
        grid.addWidget(QLabel("Driver Type:"), 4, 0)
        grid.addWidget(self._driver_combo, 4, 1)
        return g

    def _build_servo_extras_section(self):
        """Extra servo-only fields shown when Servo motor type is selected."""
        g = QGroupBox("Servo Info")
        grid = QGridLayout(g)
        grid.setHorizontalSpacing(16); grid.setVerticalSpacing(8)

        sep_lbl = QLabel("Following Error")
        sep_lbl.setStyleSheet("color:#5E81AC; font-weight:700; font-size:9pt;")
        grid.addWidget(sep_lbl, 0, 0, 1, 4)

        ul = UNIT_LABELS[self._units]
        rapid_w = _dspin(0.5, 0.0001, 9999, 4, 0.01, ul["dist"])
        feed_w  = _dspin(0.05, 0.0001, 9999, 4, 0.005, ul["dist"])
        self._w["rapid_ferror"] = rapid_w
        self._w["feed_ferror"]  = feed_w
        grid.addWidget(QLabel("Rapid Speed Following Error:"), 1, 0)
        grid.addWidget(rapid_w, 1, 1)
        grid.addWidget(QLabel("Feed Speed Following Error:"),  1, 2)
        grid.addWidget(feed_w,  1, 3)

        cb_inv_motor = QCheckBox("Invert Motor Direction")
        cb_inv_enc   = QCheckBox("Invert Encoder Direction")
        self._w["invert_motor"] = cb_inv_motor
        self._w["invert_enc"]   = cb_inv_enc
        grid.addWidget(cb_inv_motor, 2, 0, 1, 2)
        grid.addWidget(cb_inv_enc,   2, 2, 1, 2)
        return g

    # Keep old name as alias for backward compat
    def _build_servo_section(self):
        return self._build_servo_extras_section()

    def _build_scaling_section(self):
        g = QGroupBox("Scaling")
        grid = QGridLayout(g)
        grid.setHorizontalSpacing(16); grid.setVerticalSpacing(8)

        # Encoder scale (read-only, filled by dialog)
        grid.addWidget(QLabel("Encoder Scale:"), 0, 0)
        enc_s = QDoubleSpinBox()
        enc_s.setRange(-999999, 999999); enc_s.setDecimals(4); enc_s.setValue(0.0)
        enc_s.setReadOnly(True); enc_s.setMinimumWidth(120)
        enc_s.setStyleSheet("color:#A3BE8C;")
        self._w["encoder_scale"] = enc_s
        grid.addWidget(enc_s, 0, 1)

        # Stepper scale (editable, highlighted red until set)
        grid.addWidget(QLabel("Stepper Scale:"), 1, 0)
        step_s = QDoubleSpinBox()
        step_s.setRange(-999999, 999999); step_s.setDecimals(4)
        step_s.setValue(self._ax.scale); step_s.setMinimumWidth(120)
        step_s.setStyleSheet(
            "background-color:#BF616A; color:#ECEFF4; font-weight:600;")
        self._w["stepper_scale"] = step_s
        grid.addWidget(step_s, 1, 1)

        # Calculate Scale button
        btn_calc = QPushButton("Calculate Scale")
        btn_calc.setMinimumWidth(130)
        btn_calc.clicked.connect(self._open_scale_dialog)
        self._w["_btn_calc_scale"] = btn_calc
        grid.addWidget(btn_calc, 0, 2, 2, 1)

        # Max velocity / acceleration display (matches original wizard layout)
        ul = UNIT_LABELS[self._units]
        grid.addWidget(QLabel("Maximum Velocity:"), 2, 0)
        mv = _dspin(self._ax.max_velocity, 0.001, 100000, 4, 1.0, "inch/min")
        self._w["_max_vel_display"] = mv
        grid.addWidget(mv, 2, 1)

        grid.addWidget(QLabel("Maximum Acceleration:"), 3, 0)
        ma = _dspin(self._ax.max_acceleration, 0.001, 1e7, 4, 1.0, "inch/sec²")
        self._w["_max_accel_display"] = ma
        grid.addWidget(ma, 3, 1)

        # Test / Tune (disabled)
        btn_tune = QPushButton("⚙  Test / Tune Axis")
        btn_tune.setEnabled(False)
        btn_tune.setToolTip("Requires axis homed and connected")
        self._w["_btn_tune"] = btn_tune
        grid.addWidget(btn_tune, 4, 0, 1, 3)
        return g

    # ── Motion Limits ─────────────────────────────────────────────────────────
    def _build_motion_limits(self):
        g = QGroupBox("Motion Limits")
        f = QFormLayout(g)
        f.setHorizontalSpacing(16); f.setVerticalSpacing(8)
        f.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        ul = UNIT_LABELS[self._units]

        max_vel = _dspin(self._ax.max_velocity, 0.001, 99999, 4, 1.0, ul["vel"])
        self._w["max_velocity"] = max_vel
        f.addRow("Max Velocity:", max_vel)

        max_acc = _dspin(self._ax.max_acceleration, 0.001, 1e7, 4, 10.0, ul["acc"])
        self._w["max_acceleration"] = max_acc
        f.addRow("Max Acceleration:", max_acc)

        ferr = _dspin(self._ax.ferror, 0.0001, 9999, 4, 0.1, ul["dist"])
        self._w["ferror"] = ferr
        f.addRow("Following Error:", ferr)

        mferr = _dspin(self._ax.min_ferror, 0.00001, 9999, 5, 0.01, ul["dist"])
        self._w["min_ferror"] = mferr
        f.addRow("Min Following Error:", mferr)

        self._layout.addWidget(g)

    # ── Compensation ──────────────────────────────────────────────────────────
    def _build_compensation(self):
        g = QGroupBox("Compensation")
        f = QFormLayout(g)
        f.setHorizontalSpacing(16); f.setVerticalSpacing(8)
        f.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # Compensation file
        cb_use_comp = QCheckBox("Use Compensation Filename:")
        self._w["use_comp"] = cb_use_comp
        comp_edit = QLineEdit()
        comp_edit.setPlaceholderText(f"{self.letter.lower()}compensation")
        self._w["comp_file"] = comp_edit
        btn_browse = QPushButton("Browse…"); btn_browse.setMaximumWidth(80)
        btn_browse.clicked.connect(self._browse_comp_file)
        comp_type = QComboBox()
        comp_type.addItems(COMPENSATION_TYPES)
        self._w["comp_type"] = comp_type
        comp_row = QHBoxLayout()
        comp_row.addWidget(comp_edit)
        comp_row.addWidget(btn_browse)
        comp_row.addWidget(comp_type)
        f.addRow(cb_use_comp, comp_row)

        # Backlash
        cb_blash = QCheckBox("Use Backlash Compensation:")
        self._w["use_backlash"] = cb_blash
        ul = UNIT_LABELS[self._units]
        blash_spin = _dspin(0.0, 0.0, 100.0, 5, 0.001, ul["dist"])
        self._w["backlash"] = blash_spin
        f.addRow(cb_blash, blash_spin)

        # Wire enable/disable
        cb_use_comp.toggled.connect(comp_edit.setEnabled)
        cb_use_comp.toggled.connect(btn_browse.setEnabled)
        cb_use_comp.toggled.connect(comp_type.setEnabled)
        comp_edit.setEnabled(False); btn_browse.setEnabled(False)
        comp_type.setEnabled(False)

        cb_blash.toggled.connect(blash_spin.setEnabled)
        blash_spin.setEnabled(False)

        self._layout.addWidget(g)

    # ── Signals ───────────────────────────────────────────────────────────────
    def _on_motor_type_changed(self):
        is_stepper = self._motor_type_combo.currentText() == "Stepper"
        self._stepper_widget.setVisible(is_stepper)
        self._servo_widget.setVisible(not is_stepper)
        # PID group (_w entries pid_p etc) always visible — no change needed

    def _browse_comp_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, f"Select {self.letter} Axis Compensation File",
            "", "Compensation Files (*.comp *.txt);;All Files (*)")
        if path:
            self._w["comp_file"].setText(path)

    def _open_scale_dialog(self):
        dlg = AxisScaleDialog(
            axis_letter=self.letter,
            units=self._units,
            ax=self._ax,
            parent=self,
        )
        try:
            dlg.set_motion_params(
                self._w["max_velocity"].value(),
                self._w["max_acceleration"].value(),
            )
        except Exception:
            pass
        dlg.scale_applied.connect(self._on_scale_applied)
        dlg.exec()

    def _on_scale_applied(self, stepper_scale, encoder_scale):
        self._w["stepper_scale"].setValue(stepper_scale)
        self._w["stepper_scale"].setStyleSheet(
            "background-color:#2E5E2E; color:#A3BE8C; font-weight:600;")
        self._w["encoder_scale"].setValue(encoder_scale)

    # ── Data I/O ──────────────────────────────────────────────────────────────
    def load_from_axis(self, ax: AxisConfig):
        self._ax = ax
        w = self._w
        w["positive_travel"].setValue(ax.travel)
        w["final_home_pos"].setValue(ax.home_position)
        w["home_switch_loc"].setValue(ax.home_switch_location)
        w["home_search_vel"].setValue(ax.search_velocity)
        w["home_latch_vel"].setValue(ax.latch_velocity)
        idx = min(max(ax.home_sequence, 0), w["home_seq"].count() - 1)
        w["home_seq"].setCurrentIndex(idx)
        for key in ("pid_p", "pid_i", "pid_d", "pid_ff0", "pid_ff1",
                    "pid_ff2", "pid_bias", "pid_max_output"):
            if key in w:
                w[key].setValue(getattr(ax, key, 0.0))
        for key in ("step_time", "step_space", "direction_hold", "direction_setup"):
            if key in w:
                w[key].setValue(getattr(ax, key, 0))
        w["max_velocity"].setValue(ax.max_velocity)
        w["max_acceleration"].setValue(ax.max_acceleration)
        w["ferror"].setValue(ax.ferror)
        w["min_ferror"].setValue(ax.min_ferror)
        w["stepper_scale"].setValue(ax.scale)

    def save_to_axis(self, ax: AxisConfig):
        w = self._w
        ax.travel               = w["positive_travel"].value()
        ax.home_position        = w["final_home_pos"].value()
        ax.home_switch_location = w["home_switch_loc"].value()
        ax.search_velocity      = w["home_search_vel"].value()
        ax.latch_velocity       = w["home_latch_vel"].value()
        ax.home_sequence        = w["home_seq"].currentIndex()
        ax.max_velocity         = w["max_velocity"].value()
        ax.max_acceleration     = w["max_acceleration"].value()
        ax.ferror               = w["ferror"].value()
        ax.min_ferror           = w["min_ferror"].value()
        ax.scale                = w["stepper_scale"].value()
        for key in ("pid_p", "pid_i", "pid_d", "pid_ff0", "pid_ff1",
                    "pid_ff2", "pid_bias", "pid_max_output"):
            if key in w:
                setattr(ax, key, w[key].value())
        for key in ("step_time", "step_space", "direction_hold", "direction_setup"):
            if key in w:
                setattr(ax, key, w[key].value())

    def validate(self):
        w = self._w
        if w["max_velocity"].value() <= 0:
            return False, f"Axis {self.letter}: Max Velocity must be > 0."
        if w["max_acceleration"].value() <= 0:
            return False, f"Axis {self.letter}: Max Acceleration must be > 0."
        if w["ferror"].value() <= 0:
            return False, f"Axis {self.letter}: Following Error must be > 0."
        if w["stepper_scale"].value() == 0:
            return False, (f"Axis {self.letter}: Stepper Scale is zero — "
                           "use 'Calculate Scale' to set it.")
        return True, ""


# ---------------------------------------------------------------------------
# 7i76 I/O Configuration Page  (unchanged from original)
# ---------------------------------------------------------------------------

class IO7i76Page(BasePage):
    PAGE_TITLE    = "7i76 I/O Configuration"
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
        self._tb6_table = self._make_input_table(16, "TB6")
        self._tabs.addTab(self._tb6_table, "TB6 Inputs (Digital)")
        self._tb5_table = self._make_input_table(16, "TB5")
        self._tabs.addTab(self._tb5_table, "TB5 Inputs (Digital)")
        self._tb4_table = self._make_analog_table()
        self._tabs.addTab(self._tb4_table, "TB4 Analog Outputs")

    def _make_input_table(self, num_pins, prefix):
        table = QTableWidget(num_pins, 3)
        table.setHorizontalHeaderLabels(["Pin", "Function", "Invert"])
        hdr = table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        table.setColumnWidth(0, 60); table.setColumnWidth(2, 70)
        table.verticalHeader().setVisible(False)
        table.setAlternatingRowColors(True)
        for row in range(num_pins):
            item = QTableWidgetItem(f"{prefix}-{row + 1}")
            item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(row, 0, item)
            combo = QComboBox()
            combo.addItems(INPUT_FUNCTIONS)
            table.setCellWidget(row, 1, combo)
            cb_w = QWidget()
            cb_l = QHBoxLayout(cb_w)
            cb_l.setContentsMargins(0, 0, 0, 0)
            cb_l.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cb_l.addWidget(QCheckBox())
            table.setCellWidget(row, 2, cb_w)
            table.setRowHeight(row, 30)
        return table

    def _make_analog_table(self):
        table = QTableWidget(2, 4)
        table.setHorizontalHeaderLabels(["Channel", "Function", "Min V", "Max V"])
        hdr = table.horizontalHeader()
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        table.setColumnWidth(0, 70); table.setColumnWidth(2, 70); table.setColumnWidth(3, 70)
        table.verticalHeader().setVisible(False)
        table.setAlternatingRowColors(True)
        for row in range(2):
            item = QTableWidgetItem(f"AOut-{row + 1}")
            item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            table.setItem(row, 0, item)
            combo = QComboBox()
            combo.addItems(["Spindle Speed", "Unused"])
            combo.setCurrentIndex(row)
            table.setCellWidget(row, 1, combo)
            for col, val in [(2, "0.0"), (3, "10.0")]:
                i = QTableWidgetItem(val)
                i.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(row, col, i)
            table.setRowHeight(row, 30)
        return table

    def populate(self, cfg: MachineConfig): pass
    def save(self, cfg: MachineConfig): pass


# ---------------------------------------------------------------------------
# Motor Configuration Page  (full-parity wizard page)
# ---------------------------------------------------------------------------

class MotorConfigPage(BasePage):
    PAGE_TITLE    = "Motor Configuration"
    PAGE_SUBTITLE = "Set PID, stepper timing, and motion limits per axis motor"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._axis_widgets: Dict[str, AxisConfigWidget] = {}
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 16, 24, 16)
        root.setSpacing(12)

        info = QLabel(
            "Configure travel limits, homing, motor type, scaling, and motion limits per axis.")
        info.setWordWrap(True)
        info.setStyleSheet("color:#81A1C1; font-size:9pt; font-style:italic;")
        root.addWidget(info)

        self._tabs = QTabWidget()
        root.addWidget(self._tabs)

    def populate(self, cfg: MachineConfig):
        self._tabs.clear()
        self._axis_widgets.clear()
        cfg.ensure_axes()
        for letter in cfg.axis_config:
            ax = cfg.axes.get(letter, AxisConfig(name=letter))
            widget = AxisConfigWidget(letter=letter, ax=ax, units=cfg.units)
            widget.load_from_axis(ax)
            self._axis_widgets[letter] = widget
            self._tabs.addTab(widget, f"  {letter} Motor  ")

    def save(self, cfg: MachineConfig):
        cfg.ensure_axes()
        for letter, widget in self._axis_widgets.items():
            ax = cfg.axes.get(letter)
            if ax:
                widget.save_to_axis(ax)

    def validate(self):
        for letter, widget in self._axis_widgets.items():
            ok, msg = widget.validate()
            if not ok:
                return False, msg
        return True, ""


# ---------------------------------------------------------------------------
# Axis Scale Page  (standalone step, backward compatible)
# ---------------------------------------------------------------------------

class AxisScalePage(BasePage):
    PAGE_TITLE    = "Axis Scale Calculation"
    PAGE_SUBTITLE = "Calculate steps/unit from mechanical drive train parameters"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._axis_widgets: Dict = {}
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 16, 24, 16)
        root.setSpacing(12)
        info = QLabel(
            "Scale = (Motor Steps/Rev × Microstep) ÷ "
            "(Leadscrew Pitch × Pulley Ratio × Worm Ratio)")
        info.setWordWrap(True)
        info.setStyleSheet("color:#81A1C1; font-size:9.5pt; font-family:monospace;")
        root.addWidget(info)
        self._tabs = QTabWidget()
        root.addWidget(self._tabs)

    def _build_axis_tab(self, letter, ax, units):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(14)
        ws = {}

        group = QGroupBox(f"{letter} Axis Drive Train")
        grid = QGridLayout(group)
        grid.setHorizontalSpacing(20); grid.setVerticalSpacing(10)

        fields = [
            ("Motor Steps/Revolution:", "motor_steps_rev", QSpinBox, 1, 10000, 1, ""),
            ("Microstep Multiplier:",   "microstep",       QSpinBox, 1, 256,   1, "×"),
            ("Pulley Ratio:",           "pulley_ratio",    QDoubleSpinBox, 0.01, 100, 0.1, ":1"),
            ("Worm Gear Ratio:",        "worm_ratio",      QDoubleSpinBox, 0.01, 1000, 1.0, ":1"),
            ("Leadscrew Pitch:",        "leadscrew_pitch", QDoubleSpinBox, 0.001, 100, 0.5,
             "mm/rev" if units == "metric" else "in/rev"),
        ]
        for i, (label, attr, cls, mn, mx, step, suffix) in enumerate(fields):
            if cls is QSpinBox:
                spin = QSpinBox(); spin.setRange(int(mn), int(mx))
                spin.setValue(int(getattr(ax, attr, mn)))
            else:
                spin = QDoubleSpinBox(); spin.setRange(mn, mx)
                spin.setSingleStep(step); spin.setDecimals(4)
                spin.setValue(float(getattr(ax, attr, mn)))
            if suffix:
                spin.setSuffix(f"  {suffix}")
            grid.addWidget(QLabel(label), i, 0)
            grid.addWidget(spin, i, 1)
            ws[attr] = spin
            spin.valueChanged.connect(lambda _, l=letter: self._recalculate(l))
        layout.addWidget(group)

        result_frame = QGroupBox("Calculated Scale")
        rl = QHBoxLayout(result_frame)
        ws["_result_label"] = QLabel("—")
        ws["_result_label"].setStyleSheet(
            "color:#A3BE8C; font-size:14pt; font-weight:700; font-family:monospace;")
        ws["_result_label"].setAlignment(Qt.AlignmentFlag.AlignCenter)
        rl.addWidget(ws["_result_label"])
        layout.addWidget(result_frame)

        enc_group = QGroupBox("Encoder (if servo)")
        enc_grid = QGridLayout(enc_group)
        enc_spin = QSpinBox(); enc_spin.setRange(100, 100000); enc_spin.setSingleStep(100)
        enc_spin.setValue(ax.encoder_lines); enc_spin.setSuffix("  lines/rev")
        enc_grid.addWidget(QLabel("Encoder Lines:"), 0, 0)
        enc_grid.addWidget(enc_spin, 0, 1)
        ws["encoder_lines"] = enc_spin
        layout.addWidget(enc_group)
        layout.addStretch()

        self._axis_widgets[letter] = ws
        return widget

    def _recalculate(self, letter):
        ws = self._axis_widgets.get(letter)
        if not ws:
            return
        try:
            steps = ws["motor_steps_rev"].value()
            micro = ws["microstep"].value()
            pitch = ws["leadscrew_pitch"].value()
            pulley = ws["pulley_ratio"].value()
            worm = ws["worm_ratio"].value()
            denom = pitch * pulley * worm
            if not denom:
                ws["_result_label"].setText("÷0 error")
                return
            ws["_result_label"].setText(f"{(steps * micro) / denom:.4f} steps/mm")
        except Exception:
            ws["_result_label"].setText("error")

    def populate(self, cfg: MachineConfig):
        self._tabs.clear(); self._axis_widgets.clear()
        cfg.ensure_axes()
        for letter in cfg.axis_config:
            ax = cfg.axes.get(letter, AxisConfig(name=letter))
            tab = self._build_axis_tab(letter, ax, cfg.units)
            self._tabs.addTab(tab, f"{letter} Scale")
            self._recalculate(letter)

    def save(self, cfg: MachineConfig):
        cfg.ensure_axes()
        for letter, ws in self._axis_widgets.items():
            ax = cfg.axes.get(letter)
            if not ax:
                continue
            for attr in ("motor_steps_rev", "microstep", "encoder_lines"):
                if attr in ws:
                    setattr(ax, attr, ws[attr].value())
            for attr in ("pulley_ratio", "worm_ratio", "leadscrew_pitch"):
                if attr in ws:
                    setattr(ax, attr, ws[attr].value())
            try:
                d = ax.leadscrew_pitch * ax.pulley_ratio * ax.worm_ratio
                if d:
                    ax.scale = (ax.motor_steps_rev * ax.microstep) / d
            except Exception:
                pass
