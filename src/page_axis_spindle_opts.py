"""
Axis Configuration Page
Spindle Configuration Page
Options Page          ← FULL PnCconf parity (HALUI, ClassicLadder, Custom HAL)
Realtime Components Page ← FULL PnCconf parity (instance counts, threads, custom table)
"""
from __future__ import annotations

from typing import Dict, List, Any

try:
    from PyQt6.QtWidgets import (
        QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
        QLabel, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox,
        QGroupBox, QCheckBox, QTabWidget, QWidget, QPushButton,
        QListWidget, QListWidgetItem, QTextEdit, QRadioButton,
        QButtonGroup, QFileDialog, QTableWidget, QTableWidgetItem,
        QHeaderView, QScrollArea, QFrame, QSizePolicy, QAbstractItemView,
    )
    from PyQt6.QtCore import Qt, pyqtSignal as Signal
    from PyQt6.QtGui import QFont
except ImportError:
    from PySide6.QtWidgets import (
        QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
        QLabel, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox,
        QGroupBox, QCheckBox, QTabWidget, QWidget, QPushButton,
        QListWidget, QListWidgetItem, QTextEdit, QRadioButton,
        QButtonGroup, QFileDialog, QTableWidget, QTableWidgetItem,
        QHeaderView, QScrollArea, QFrame, QSizePolicy, QAbstractItemView,
    )
    from PySide6.QtCore import Qt, Signal
    from PySide6.QtGui import QFont

from pages.base_page import BasePage
from config.machine_config import MachineConfig, AxisConfig


# ─────────────────────────────────────────────────────────────────────────────
# Axis Configuration Page  (unchanged functional content)
# ─────────────────────────────────────────────────────────────────────────────

class AxisConfigPage(BasePage):
    PAGE_TITLE    = "Axis Configuration"
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

        travel_group = QGroupBox("Travel & Home Position")
        travel_grid  = QGridLayout(travel_group)
        travel_grid.setHorizontalSpacing(16)
        travel_grid.setVerticalSpacing(10)

        for i, (label, attr, mn, mx, suffix) in enumerate([
            ("Travel Distance:",      "travel",              0.001, 10000, "mm"),
            ("Home Position:",        "home_position",       -9999, 9999,  "mm"),
            ("Home Switch Location:", "home_switch_location",-9999, 9999,  "mm"),
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

        home_group = QGroupBox("Homing Parameters")
        home_grid  = QGridLayout(home_group)
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

        hint = QLabel("-1 = No homing,  0 = Home simultaneously,  1+ = Home in order")
        hint.setStyleSheet("color:#4C566A; font-size:8.5pt;")
        home_grid.addWidget(hint, 3, 0, 1, 2)
        layout.addWidget(home_group)
        layout.addStretch()

        self._axis_widgets[letter] = ws
        return widget

    def populate(self, cfg: MachineConfig):
        self._tabs.clear(); self._axis_widgets.clear()
        for letter in cfg.axis_config:
            ax  = cfg.axes.get(letter, AxisConfig(name=letter))
            tab = self._build_axis_tab(letter, ax)
            self._tabs.addTab(tab, f"{letter} Axis")

    def save(self, cfg: MachineConfig):
        for letter, ws in self._axis_widgets.items():
            ax = cfg.axes.get(letter)
            if not ax:
                continue
            for attr, widget in ws.items():
                if isinstance(widget, (QDoubleSpinBox, QSpinBox)):
                    setattr(ax, attr, widget.value())


# ─────────────────────────────────────────────────────────────────────────────
# Spindle Configuration Page  (unchanged)
# ─────────────────────────────────────────────────────────────────────────────

class SpindleConfigPage(BasePage):
    PAGE_TITLE    = "Spindle Configuration"
    PAGE_SUBTITLE = "Configure spindle speed, encoder, and analog output parameters"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 24, 32, 24)
        root.setSpacing(16)

        analog_group = QGroupBox("Analog Spindle Output")
        ag = QGridLayout(analog_group)
        ag.setHorizontalSpacing(16); ag.setVerticalSpacing(10)

        self._max_voltage  = self._dspin(10.0, 0, 15, suffix=" V")
        self._min_rpm      = self._dspin(0, 0, 100000, suffix=" RPM")
        self._max_rpm      = self._dspin(3000, 1, 100000, suffix=" RPM")
        self._acceleration = self._dspin(200, 1, 100000, suffix=" RPM/s")

        for row, (lbl, w) in enumerate([
            ("Analog Max Voltage:", self._max_voltage),
            ("Min RPM:",            self._min_rpm),
            ("Max RPM:",            self._max_rpm),
            ("Acceleration:",       self._acceleration),
        ]):
            ag.addWidget(QLabel(lbl), row, 0)
            ag.addWidget(w, row, 1)
        root.addWidget(analog_group)

        enc_group = QGroupBox("Spindle Encoder")
        eg = QGridLayout(enc_group)
        eg.setHorizontalSpacing(16); eg.setVerticalSpacing(10)
        self._use_encoder      = QCheckBox("Use spindle encoder for speed feedback")
        self._encoder_scale    = self._dspin(100, 1, 100000, suffix=" counts/rev")
        self._spindle_at_speed = QCheckBox("Wait for spindle at speed")
        eg.addWidget(self._use_encoder, 0, 0, 1, 2)
        eg.addWidget(QLabel("Encoder Scale:"), 1, 0)
        eg.addWidget(self._encoder_scale, 1, 1)
        eg.addWidget(self._spindle_at_speed, 2, 0, 1, 2)
        root.addWidget(enc_group)
        root.addStretch()

    @staticmethod
    def _dspin(value, lo, hi, decimals=1, suffix=""):
        s = QDoubleSpinBox()
        s.setRange(lo, hi); s.setDecimals(decimals); s.setValue(value)
        if suffix: s.setSuffix(suffix)
        return s

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
        sp.min_rpm            = self._min_rpm.value()
        sp.max_rpm            = self._max_rpm.value()
        sp.acceleration       = self._acceleration.value()
        sp.use_encoder        = self._use_encoder.isChecked()
        sp.encoder_scale      = self._encoder_scale.value()
        sp.spindle_at_speed   = self._spindle_at_speed.isChecked()


# ─────────────────────────────────────────────────────────────────────────────
# HALUI MDI Command widget  (reusable row widget)
# ─────────────────────────────────────────────────────────────────────────────

class _HaluiRow(QWidget):
    """Single HALUI MDI command row: label + QLineEdit."""
    def __init__(self, index: int, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        # HAL pin name
        self._lbl = QLabel(f"Cmd{index + 1:02d}")
        self._lbl.setFixedWidth(48)
        self._lbl.setStyleSheet("color:#81A1C1; font-family:monospace; font-size:9pt;")
        # HAL pin label
        self._pin_lbl = QLabel(f"halui.mdi-command-{index:02d}")
        self._pin_lbl.setFixedWidth(180)
        self._pin_lbl.setStyleSheet("color:#4C566A; font-size:8.5pt; font-family:monospace;")
        # G-code input
        self._edit = QLineEdit()
        self._edit.setPlaceholderText("G-code command, e.g.  G0 Z10")
        layout.addWidget(self._lbl)
        layout.addWidget(self._pin_lbl)
        layout.addWidget(self._edit, 1)

    def command(self) -> str:
        return self._edit.text().strip()

    def set_command(self, text: str):
        self._edit.setText(text)

    def update_index(self, index: int):
        self._lbl.setText(f"Cmd{index + 1:02d}")
        self._pin_lbl.setText(f"halui.mdi-command-{index:02d}")


# ─────────────────────────────────────────────────────────────────────────────
# Options Page  — FULL PnCconf parity
# ─────────────────────────────────────────────────────────────────────────────

class OptionsPage(BasePage):
    PAGE_TITLE    = "Options"
    PAGE_SUBTITLE = "HALUI MDI commands, ClassicLadder PLC, and custom HAL snippets"

    MAX_HALUI_COMMANDS = 15

    def __init__(self, parent=None):
        super().__init__(parent)
        self._halui_rows: List[_HaluiRow] = []
        self._build_ui()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # Outer scroll area so the page doesn't clip
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        root = QVBoxLayout(container)
        root.setContentsMargins(24, 16, 24, 16)
        root.setSpacing(16)

        self._build_halui_section(root)
        self._build_classicladder_section(root)
        self._build_custom_hal_section(root)

        root.addStretch()
        scroll.setWidget(container)

        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.addWidget(scroll)

    # ── HALUI MDI Commands ────────────────────────────────────────────────────

    def _build_halui_section(self, parent_layout: QVBoxLayout):
        g = QGroupBox("HALUI MDI Commands")
        g_layout = QVBoxLayout(g)
        g_layout.setSpacing(8)

        # Info header
        info = QLabel(
            "Up to 15 MDI commands mapped to  halui.mdi-command-00  …  halui.mdi-command-14\n"
            "Each command is triggered by connecting a HAL bit pin to the corresponding signal."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color:#81A1C1; font-size:8.5pt;")
        g_layout.addWidget(info)

        # Column headers
        hdr = QHBoxLayout()
        for text, width in [("Index", 48), ("HAL Pin", 180), ("G-code Command", -1)]:
            lbl = QLabel(text)
            lbl.setStyleSheet(
                "color:#5E81AC; font-weight:700; font-size:8pt; "
                "text-transform:uppercase; letter-spacing:0.3px;")
            if width > 0:
                lbl.setFixedWidth(width)
            hdr.addWidget(lbl, 0 if width > 0 else 1)
        g_layout.addLayout(hdr)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color:#3A3A50;")
        g_layout.addWidget(sep)

        # Scrollable command list
        self._halui_scroll = QScrollArea()
        self._halui_scroll.setWidgetResizable(True)
        self._halui_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._halui_scroll.setMinimumHeight(120)
        self._halui_scroll.setMaximumHeight(340)

        self._halui_container = QWidget()
        self._halui_rows_layout = QVBoxLayout(self._halui_container)
        self._halui_rows_layout.setSpacing(4)
        self._halui_rows_layout.setContentsMargins(0, 0, 0, 0)
        self._halui_rows_layout.addStretch()

        self._halui_scroll.setWidget(self._halui_container)
        g_layout.addWidget(self._halui_scroll)

        # Count label
        self._halui_count_lbl = QLabel("0 / 15 commands")
        self._halui_count_lbl.setStyleSheet("color:#4C566A; font-size:8.5pt;")

        # Buttons
        btn_add    = QPushButton("＋  Add Command")
        btn_remove = QPushButton("－  Remove Last")
        btn_add.setFixedWidth(140)
        btn_remove.setFixedWidth(140)
        btn_add.clicked.connect(self._halui_add)
        btn_remove.clicked.connect(self._halui_remove)

        btn_row = QHBoxLayout()
        btn_row.addWidget(btn_add)
        btn_row.addWidget(btn_remove)
        btn_row.addStretch()
        btn_row.addWidget(self._halui_count_lbl)

        g_layout.addLayout(btn_row)
        parent_layout.addWidget(g)

    def _halui_add(self):
        if len(self._halui_rows) >= self.MAX_HALUI_COMMANDS:
            return
        idx = len(self._halui_rows)
        row = _HaluiRow(idx)
        self._halui_rows.append(row)
        # Insert before the stretch
        self._halui_rows_layout.insertWidget(
            self._halui_rows_layout.count() - 1, row)
        self._halui_update_count()

    def _halui_remove(self):
        if not self._halui_rows:
            return
        row = self._halui_rows.pop()
        self._halui_rows_layout.removeWidget(row)
        row.setParent(None)
        row.deleteLater()
        self._halui_update_count()

    def _halui_update_count(self):
        n = len(self._halui_rows)
        self._halui_count_lbl.setText(f"{n} / {self.MAX_HALUI_COMMANDS} commands")
        # Disable Add when at limit
        # We find the button via parent traversal — simpler to store ref
        # Already stored via closure in _build_halui_section; re-fetch from parent
        # Approach: store on self
        if hasattr(self, "_btn_halui_add"):
            self._btn_halui_add.setEnabled(n < self.MAX_HALUI_COMMANDS)

    def _halui_set_commands(self, commands: List[str]):
        """Load a list of commands into the row widgets."""
        # Clear
        for row in self._halui_rows:
            self._halui_rows_layout.removeWidget(row)
            row.setParent(None)
            row.deleteLater()
        self._halui_rows.clear()
        # Re-add
        for cmd in commands[:self.MAX_HALUI_COMMANDS]:
            idx = len(self._halui_rows)
            row = _HaluiRow(idx)
            row.set_command(cmd)
            self._halui_rows.append(row)
            self._halui_rows_layout.insertWidget(
                self._halui_rows_layout.count() - 1, row)
        self._halui_update_count()

    # ── ClassicLadder PLC ─────────────────────────────────────────────────────

    def _build_classicladder_section(self, parent_layout: QVBoxLayout):
        g = QGroupBox("ClassicLadder PLC")
        g_layout = QVBoxLayout(g)
        g_layout.setSpacing(10)

        # Master enable
        self._cl_enable = QCheckBox("Include ClassicLadder PLC in configuration")
        self._cl_enable.setStyleSheet("font-weight:600;")
        g_layout.addWidget(self._cl_enable)

        # Separator
        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color:#3A3A50;")
        g_layout.addWidget(sep)

        # Ladder program type radio group
        type_label = QLabel("Ladder Program Type:")
        type_label.setStyleSheet("color:#A0C4E8; font-weight:600;")
        g_layout.addWidget(type_label)

        self._cl_btn_group = QButtonGroup(self)

        radio_defs = [
            ("none",         "External ladder program  (load from file)"),
            ("blank",        "Blank ladder program  (empty, for custom editing)"),
            ("estop",        "E-stop ladder program  (standard e-stop interlock)"),
            ("serialmodbus", "Serial Modbus program  (Modbus RTU/ASCII master)"),
            ("custom",       "Custom ladder program  (specify file path below)"),
        ]
        self._cl_radios: Dict[str, QRadioButton] = {}
        for key, label in radio_defs:
            rb = QRadioButton(label)
            self._cl_radios[key] = rb
            self._cl_btn_group.addButton(rb)
            g_layout.addWidget(rb)

        self._cl_radios["none"].setChecked(True)

        # HAL connections checkbox
        self._cl_hal_connections = QCheckBox(
            "Include connections to HAL  "
            "(wire ClassicLadder I/O to HAL signals)")
        self._cl_hal_connections.setStyleSheet("color:#ECEFF4; margin-left:16px;")
        g_layout.addWidget(self._cl_hal_connections)

        # File picker (enabled only when "custom" or "none" selected)
        file_frame = QWidget()
        file_row   = QHBoxLayout(file_frame)
        file_row.setContentsMargins(0, 0, 0, 0)
        file_row.setSpacing(8)

        self._cl_file_label = QLabel("Ladder file path:")
        self._cl_file_label.setFixedWidth(130)
        self._cl_program_edit = QLineEdit()
        self._cl_program_edit.setPlaceholderText(
            "path/to/my_ladder.clp  (required for External or Custom)")
        self._cl_browse_btn = QPushButton("Browse…")
        self._cl_browse_btn.setFixedWidth(90)
        self._cl_browse_btn.clicked.connect(self._browse_ladder_file)

        file_row.addWidget(self._cl_file_label)
        file_row.addWidget(self._cl_program_edit, 1)
        file_row.addWidget(self._cl_browse_btn)
        g_layout.addWidget(file_frame)

        # Modbus sub-options (shown only for serialmodbus)
        self._cl_modbus_frame = QGroupBox("Serial Modbus Options")
        mb_form = QFormLayout(self._cl_modbus_frame)
        mb_form.setHorizontalSpacing(16)
        mb_form.setVerticalSpacing(8)

        self._cl_modbus_port  = QLineEdit("/dev/ttyS0")
        self._cl_modbus_baud  = QComboBox()
        self._cl_modbus_baud.addItems(
            ["9600", "19200", "38400", "57600", "115200"])
        self._cl_modbus_parity = QComboBox()
        self._cl_modbus_parity.addItems(["None", "Even", "Odd"])
        self._cl_modbus_stopbits = QComboBox()
        self._cl_modbus_stopbits.addItems(["1", "2"])

        mb_form.addRow("Serial Port:", self._cl_modbus_port)
        mb_form.addRow("Baud Rate:", self._cl_modbus_baud)
        mb_form.addRow("Parity:", self._cl_modbus_parity)
        mb_form.addRow("Stop Bits:", self._cl_modbus_stopbits)
        g_layout.addWidget(self._cl_modbus_frame)

        parent_layout.addWidget(g)

        # ── Signal wiring ─────────────────────────────────────────────────────
        self._cl_enable.toggled.connect(self._on_cl_enable_changed)
        for rb in self._cl_radios.values():
            rb.toggled.connect(self._on_cl_type_changed)

        self._on_cl_enable_changed(False)

    def _on_cl_enable_changed(self, enabled: bool):
        """Enable/disable entire ClassicLadder sub-section."""
        for rb in self._cl_radios.values():
            rb.setEnabled(enabled)
        self._cl_hal_connections.setEnabled(enabled)
        self._on_cl_type_changed()   # re-evaluate file picker state

    def _on_cl_type_changed(self):
        """Show/hide file picker and modbus options based on selected type."""
        enabled    = self._cl_enable.isChecked()
        cl_type    = self._cl_selected_type()
        needs_file = cl_type in ("none", "custom")    # these need a file path
        is_modbus  = cl_type == "serialmodbus"

        self._cl_program_edit.setEnabled(enabled and needs_file)
        self._cl_browse_btn.setEnabled(enabled and needs_file)
        self._cl_file_label.setEnabled(enabled and needs_file)
        self._cl_modbus_frame.setVisible(enabled and is_modbus)

    def _cl_selected_type(self) -> str:
        for key, rb in self._cl_radios.items():
            if rb.isChecked():
                return key
        return "none"

    def _browse_ladder_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select ClassicLadder Program",
            "", "ClassicLadder Files (*.clp);;All Files (*)")
        if path:
            self._cl_program_edit.setText(path)

    # ── Custom HAL Snippets ───────────────────────────────────────────────────

    def _build_custom_hal_section(self, parent_layout: QVBoxLayout):
        g = QGroupBox("Custom HAL Snippets")
        g_layout = QVBoxLayout(g)
        g_layout.setSpacing(8)

        info = QLabel(
            "These snippets are injected verbatim into the generated .hal file.\n"
            "'Before nets' runs before all component connections; "
            "'After nets' runs after all connections are made.")
        info.setWordWrap(True)
        info.setStyleSheet("color:#81A1C1; font-size:8.5pt;")
        g_layout.addWidget(info)

        g_layout.addWidget(self._section_label(
            "Custom HAL  (inserted BEFORE main nets):"))
        self._custom_hal_before = QTextEdit()
        self._custom_hal_before.setMinimumHeight(80)
        self._custom_hal_before.setMaximumHeight(130)
        self._custom_hal_before.setPlaceholderText(
            "# loadrt  my_component\n"
            "# setp    my_component.param  1.0")
        self._custom_hal_before.setFont(self._mono_font())
        g_layout.addWidget(self._custom_hal_before)

        g_layout.addWidget(self._section_label(
            "Custom HAL  (inserted AFTER main nets):"))
        self._custom_hal_after = QTextEdit()
        self._custom_hal_after.setMinimumHeight(80)
        self._custom_hal_after.setMaximumHeight(130)
        self._custom_hal_after.setPlaceholderText(
            "# net  my-signal  my_component.out  => motion.sync-in\n"
            "# addf my_component.update  servo-thread")
        self._custom_hal_after.setFont(self._mono_font())
        g_layout.addWidget(self._custom_hal_after)

        parent_layout.addWidget(g)

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _section_label(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            "color:#5E81AC; font-weight:700; font-size:9pt;")
        return lbl

    @staticmethod
    def _mono_font() -> QFont:
        f = QFont("Courier New")
        f.setPointSize(9)
        return f

    # ── Populate / Save ───────────────────────────────────────────────────────

    def populate(self, cfg: MachineConfig):
        o = cfg.options
        # HALUI
        self._halui_set_commands(o.halui_commands)
        # ClassicLadder
        self._cl_enable.setChecked(o.use_classicladder)
        cl_type = getattr(o, "classicladder_type", "none")
        if cl_type in self._cl_radios:
            self._cl_radios[cl_type].setChecked(True)
        else:
            self._cl_radios["none"].setChecked(True)
        self._cl_hal_connections.setChecked(
            getattr(o, "classicladder_use_hal_connections", False))
        self._cl_program_edit.setText(o.classicladder_program)
        # Custom HAL
        self._custom_hal_before.setPlainText(o.custom_hal_before)
        self._custom_hal_after.setPlainText(o.custom_hal_after)
        # Trigger visibility update
        self._on_cl_enable_changed(o.use_classicladder)

    def save(self, cfg: MachineConfig):
        o = cfg.options
        # HALUI
        o.halui_commands    = [r.command() for r in self._halui_rows if r.command()]
        o.num_halui_commands = len(o.halui_commands)
        # ClassicLadder
        o.use_classicladder = self._cl_enable.isChecked()
        o.classicladder_type = self._cl_selected_type()
        o.classicladder_program = self._cl_program_edit.text()
        o.classicladder_use_hal_connections = self._cl_hal_connections.isChecked()
        # Custom HAL
        o.custom_hal_before = self._custom_hal_before.toPlainText()
        o.custom_hal_after  = self._custom_hal_after.toPlainText()

    def validate(self):
        o_type = self._cl_selected_type()
        if self._cl_enable.isChecked() and o_type in ("none", "custom"):
            if not self._cl_program_edit.text().strip():
                return False, (
                    "ClassicLadder: A ladder file path is required for "
                    "'External' or 'Custom' program types.")
        return True, ""


# ─────────────────────────────────────────────────────────────────────────────
# Realtime Components Page  — FULL PnCconf parity
# ─────────────────────────────────────────────────────────────────────────────

# Component catalog: (name, description, allowed_threads, servo_only)
#   allowed_threads: "both" | "servo" | "base"
_COMPONENT_CATALOG = [
    # name              description                                    threads   servo_only
    ("absolute",        "Compute absolute value of a float signal",   "both",   False),
    ("pid",             "PID controller  (closed-loop servo control)","servo",  True),
    ("scale",           "Scale a signal by a constant factor",        "both",   False),
    ("mux2",            "2-input multiplexer",                        "both",   False),
    ("mux4",            "4-input multiplexer",                        "both",   False),
    ("mux8",            "8-input multiplexer",                        "both",   False),
    ("mux16",           "16-input multiplexer",                       "both",   False),
    ("lowpass",         "Low-pass filter  (noise smoothing)",         "both",   False),
    ("limit1",          "Limit a signal to a range  (1st order)",     "both",   False),
    ("limit2",          "Limit with rate limiting  (2nd order)",      "both",   False),
    ("limit3",          "Limit with accel limiting  (3rd order)",     "servo",  True),
    ("not",             "Boolean NOT gate",                           "both",   False),
    ("and2",            "2-input AND gate",                           "both",   False),
    ("or2",             "2-input OR gate",                            "both",   False),
    ("xor2",            "2-input XOR gate",                           "both",   False),
    ("estop_latch",     "Latching E-stop logic",                      "servo",  True),
    ("logic",           "Combinational logic (configurable)",         "both",   False),
    ("oneshot",         "One-shot pulse generator",                   "both",   False),
    ("toggle",          "Toggle flip-flop on rising edge",            "both",   False),
    ("near",            "Test if two values are near each other",     "servo",  True),
    ("sum2",            "Sum of two signals with gains",              "both",   False),
    ("wcomp",           "Window comparator",                          "servo",  True),
    ("conv_float_s32",  "Convert float → s32",                        "both",   False),
    ("conv_s32_float",  "Convert s32 → float",                        "both",   False),
    ("conv_bit_s32",    "Convert bit → s32",                          "both",   False),
    ("conv_s32_bit",    "Convert s32 → bit",                          "both",   False),
]

_THREAD_OPTIONS = ["servo-thread", "base-thread"]


class _ComponentRow(QWidget):
    """
    One row in the realtime component panel:
      [name label]  [description]  [count spinbox]  [thread dropdown]  [lock icon]
    """
    def __init__(self, name: str, description: str,
                 allowed: str, servo_only: bool, parent=None):
        super().__init__(parent)
        self._name       = name
        self._allowed    = allowed   # "both" | "servo" | "base"
        self._servo_only = servo_only

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(10)

        # Component name (monospace, fixed width)
        self._name_lbl = QLabel(name)
        self._name_lbl.setFixedWidth(150)
        self._name_lbl.setStyleSheet(
            "color:#A3BE8C; font-family:'Courier New',monospace; font-size:9.5pt;")

        # Description
        self._desc_lbl = QLabel(description)
        self._desc_lbl.setStyleSheet("color:#81A1C1; font-size:8.5pt;")
        self._desc_lbl.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        # Instance count spinbox
        self._count = QSpinBox()
        self._count.setRange(0, 32)
        self._count.setValue(0)
        self._count.setFixedWidth(60)
        self._count.setToolTip(
            "Number of instances to load  (0 = don't load this component)")
        self._count.setStyleSheet(
            "QSpinBox { min-height: 26px; }")

        # Thread selector
        self._thread = QComboBox()
        self._thread.setFixedWidth(120)
        if allowed == "servo":
            self._thread.addItem("servo-thread")
            self._thread.setEnabled(False)
            self._thread.setToolTip("This component must run in the servo thread")
        elif allowed == "base":
            self._thread.addItem("base-thread")
            self._thread.setEnabled(False)
            self._thread.setToolTip("This component must run in the base thread")
        else:
            self._thread.addItems(_THREAD_OPTIONS)
            self._thread.setToolTip("Select which HAL thread to addf this component to")

        # Lock icon for servo-only
        lock_lbl = QLabel()
        if servo_only:
            lock_lbl.setText("🔒")
            lock_lbl.setToolTip("Servo thread only — cannot run in base thread")
            lock_lbl.setStyleSheet("font-size:10pt;")
        lock_lbl.setFixedWidth(20)

        layout.addWidget(self._name_lbl)
        layout.addWidget(self._desc_lbl, 1)
        layout.addWidget(QLabel("×"))
        layout.addWidget(self._count)
        layout.addWidget(self._thread)
        layout.addWidget(lock_lbl)

        # Dim the row when count = 0
        self._count.valueChanged.connect(self._on_count_changed)
        self._on_count_changed(0)

    def _on_count_changed(self, value: int):
        active = value > 0
        self._desc_lbl.setStyleSheet(
            f"color:{'#81A1C1' if active else '#4C566A'}; font-size:8.5pt;")
        self._name_lbl.setStyleSheet(
            f"color:{'#A3BE8C' if active else '#4C566A'}; "
            f"font-family:'Courier New',monospace; font-size:9.5pt;")
        self._thread.setEnabled(active and self._allowed == "both")

    @property
    def name(self) -> str:
        return self._name

    def count(self) -> int:
        return self._count.value()

    def set_count(self, v: int):
        self._count.setValue(v)

    def thread(self) -> str:
        return self._thread.currentText()

    def set_thread(self, t: str):
        idx = self._thread.findText(t)
        if idx >= 0:
            self._thread.setCurrentIndex(idx)


class RealtimePage(BasePage):
    PAGE_TITLE    = "Realtime Components"
    PAGE_SUBTITLE = "Select additional HAL real-time kernel modules to load"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._comp_rows: Dict[str, _ComponentRow] = {}
        self._build_ui()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        root = QVBoxLayout(container)
        root.setContentsMargins(24, 16, 24, 16)
        root.setSpacing(16)

        self._build_std_components(root)
        self._build_custom_commands(root)

        root.addStretch()
        scroll.setWidget(container)

        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.addWidget(scroll)

    # ── Standard components ───────────────────────────────────────────────────

    def _build_std_components(self, parent: QVBoxLayout):
        g = QGroupBox("Standard HAL Realtime Components")
        g_layout = QVBoxLayout(g)
        g_layout.setSpacing(2)

        # Column header
        hdr = QWidget()
        hdr_layout = QHBoxLayout(hdr)
        hdr_layout.setContentsMargins(4, 4, 4, 4)
        hdr_layout.setSpacing(10)

        for text, width, stretch in [
            ("Component",   150, 0),
            ("Description", -1,  1),
            ("×",           12,  0),
            ("Instances",   60,  0),
            ("Thread",      120, 0),
            ("",            20,  0),
        ]:
            lbl = QLabel(text)
            lbl.setStyleSheet(
                "color:#5E81AC; font-weight:700; font-size:8pt; "
                "letter-spacing:0.3px;")
            if width > 0:
                lbl.setFixedWidth(width)
            hdr_layout.addWidget(lbl, stretch)

        g_layout.addWidget(hdr)

        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color:#3A3A50;")
        g_layout.addWidget(sep)

        # Alternating row colors via setStyleSheet on odd-index rows
        for i, (name, desc, allowed, servo_only) in enumerate(_COMPONENT_CATALOG):
            row = _ComponentRow(name, desc, allowed, servo_only)
            if i % 2 == 1:
                row.setStyleSheet("background-color:#222230; border-radius:3px;")
            self._comp_rows[name] = row
            g_layout.addWidget(row)

        # Quick-select buttons
        btn_row = QHBoxLayout()
        btn_none = QPushButton("Deselect All")
        btn_servo = QPushButton("Enable Servo Defaults")
        btn_none.setFixedWidth(120)
        btn_servo.setFixedWidth(160)
        btn_none.setToolTip("Set all instance counts to 0")
        btn_servo.setToolTip(
            "Enable the typical set for closed-loop servo: pid, scale, limit3, near")
        btn_none.clicked.connect(self._deselect_all)
        btn_servo.clicked.connect(self._enable_servo_defaults)
        btn_row.addWidget(btn_none)
        btn_row.addWidget(btn_servo)
        btn_row.addStretch()

        g_layout.addLayout(btn_row)
        parent.addWidget(g)

    def _deselect_all(self):
        for row in self._comp_rows.values():
            row.set_count(0)

    def _enable_servo_defaults(self):
        defaults = {
            "pid":   1,
            "scale": 2,
            "limit3": 1,
            "near":  1,
            "estop_latch": 1,
        }
        for name, count in defaults.items():
            if name in self._comp_rows:
                self._comp_rows[name].set_count(count)

    # ── Custom component commands ─────────────────────────────────────────────

    def _build_custom_commands(self, parent: QVBoxLayout):
        g = QGroupBox("Custom Component Commands")
        g_layout = QVBoxLayout(g)
        g_layout.setSpacing(8)

        info = QLabel(
            "Add custom  loadrt  and  addf  commands for components not listed above.\n"
            "These are appended verbatim to the generated HAL file."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color:#81A1C1; font-size:8.5pt;")
        g_layout.addWidget(info)

        # Table
        self._cmd_table = QTableWidget(0, 3)
        self._cmd_table.setHorizontalHeaderLabels(
            ["Load Command", "Thread Command (addf)", "Thread"])
        hdr = self._cmd_table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self._cmd_table.setColumnWidth(2, 130)
        self._cmd_table.verticalHeader().setDefaultSectionSize(30)
        self._cmd_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows)
        self._cmd_table.setAlternatingRowColors(True)
        self._cmd_table.setMinimumHeight(120)
        self._cmd_table.setMaximumHeight(240)
        g_layout.addWidget(self._cmd_table)

        # Buttons
        btn_row = QHBoxLayout()
        btn_add    = QPushButton("＋  Add Row")
        btn_remove = QPushButton("－  Remove Row")
        btn_add.setFixedWidth(110)
        btn_remove.setFixedWidth(110)
        btn_add.clicked.connect(self._add_cmd_row)
        btn_remove.clicked.connect(self._remove_cmd_row)
        btn_row.addWidget(btn_add)
        btn_row.addWidget(btn_remove)
        btn_row.addStretch()

        # Thread hint
        hint = QLabel(
            "Tip: 'Load Command' example:  loadrt  my_comp count=1\n"
            "      'Thread Command' example:  addf  my_comp.0  servo-thread")
        hint.setStyleSheet("color:#4C566A; font-size:8pt;")
        hint.setWordWrap(True)

        g_layout.addLayout(btn_row)
        g_layout.addWidget(hint)
        parent.addWidget(g)

    def _add_cmd_row(self):
        row = self._cmd_table.rowCount()
        self._cmd_table.insertRow(row)

        load_item   = QTableWidgetItem("loadrt  ")
        thread_item = QTableWidgetItem("addf  ")
        self._cmd_table.setItem(row, 0, load_item)
        self._cmd_table.setItem(row, 1, thread_item)

        thread_combo = QComboBox()
        thread_combo.addItems(["servo-thread", "base-thread"])
        self._cmd_table.setCellWidget(row, 2, thread_combo)

    def _remove_cmd_row(self):
        selected = self._cmd_table.selectedItems()
        if selected:
            self._cmd_table.removeRow(self._cmd_table.currentRow())
        elif self._cmd_table.rowCount() > 0:
            self._cmd_table.removeRow(self._cmd_table.rowCount() - 1)

    # ── Populate / Save ───────────────────────────────────────────────────────

    def populate(self, cfg: MachineConfig):
        rt = cfg.realtime

        # Standard components — read count_ and thread_ attributes
        for name, row in self._comp_rows.items():
            count_attr  = f"count_{name}"
            thread_attr = f"thread_{name}"
            row.set_count(getattr(rt, count_attr, 0))
            row.set_thread(getattr(rt, thread_attr, "servo-thread"))

        # Custom command rows
        self._cmd_table.setRowCount(0)
        for entry in getattr(rt, "custom_components", []):
            if isinstance(entry, dict):
                self._restore_cmd_row(
                    entry.get("load_cmd", ""),
                    entry.get("thread_cmd", ""),
                    entry.get("thread", "servo-thread"),
                )
            elif isinstance(entry, str) and entry.strip():
                # Legacy: plain string — treat as load command
                self._restore_cmd_row(entry, "", "servo-thread")

    def _restore_cmd_row(self, load_cmd: str, thread_cmd: str, thread: str):
        row = self._cmd_table.rowCount()
        self._cmd_table.insertRow(row)
        self._cmd_table.setItem(row, 0, QTableWidgetItem(load_cmd))
        self._cmd_table.setItem(row, 1, QTableWidgetItem(thread_cmd))
        combo = QComboBox()
        combo.addItems(["servo-thread", "base-thread"])
        idx = combo.findText(thread)
        if idx >= 0:
            combo.setCurrentIndex(idx)
        self._cmd_table.setCellWidget(row, 2, combo)

    def save(self, cfg: MachineConfig):
        rt = cfg.realtime

        # Standard components
        for name, row in self._comp_rows.items():
            setattr(rt, f"count_{name}",  row.count())
            setattr(rt, f"thread_{name}", row.thread())

        # Custom command rows → list of dicts
        custom = []
        for r in range(self._cmd_table.rowCount()):
            load_item   = self._cmd_table.item(r, 0)
            thread_item = self._cmd_table.item(r, 1)
            combo       = self._cmd_table.cellWidget(r, 2)
            load_cmd    = load_item.text().strip()  if load_item   else ""
            thread_cmd  = thread_item.text().strip() if thread_item else ""
            thread      = combo.currentText() if combo else "servo-thread"
            if load_cmd:
                custom.append({
                    "load_cmd":   load_cmd,
                    "thread_cmd": thread_cmd,
                    "thread":     thread,
                })
        rt.custom_components = custom

    def validate(self):
        for name, row in self._comp_rows.items():
            if row.count() < 0:
                return False, f"Component '{name}': instance count cannot be negative."
        return True, ""
