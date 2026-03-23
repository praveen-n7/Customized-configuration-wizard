"""
Mesa Connector Pin Assignment Page — Full Feature Parity
=========================================================
Replicates ALL behavior of the original LinuxCNC GTK PnCConf
"Connector Pin Assign" step:

  • Tab per connector (P2, P3, …) drawn from firmware spec
  • Table columns: Pin #, Function (dropdown), Type (auto+editable), Invert
  • Function dropdown uses the complete PIN_FUNCTION_CATALOG
  • Type auto-updates when function changes
  • Allocation tracking — stepgen/encoder counts enforce firmware limits
  • Duplicate detection — same signal on two pins → red highlight + error
  • HAL preview column shows exact hm2_* pin path for each assignment
  • validate() returns errors preventing navigation until resolved
  • Smart Serial summary tab when SS ports > 0
"""
from __future__ import annotations
from typing import Dict, List, Optional, Set

try:
    from PyQt6.QtWidgets import (
        QVBoxLayout, QHBoxLayout, QLabel, QTabWidget,
        QTableWidget, QTableWidgetItem, QHeaderView,
        QComboBox, QCheckBox, QWidget, QFrame,
        QSizePolicy, QMessageBox, QGroupBox, QTextEdit,
        QPushButton,
    )
    from PyQt6.QtCore import Qt, QTimer
    from PyQt6.QtGui import QColor, QBrush, QFont
except ImportError:
    from PySide6.QtWidgets import (
        QVBoxLayout, QHBoxLayout, QLabel, QTabWidget,
        QTableWidget, QTableWidgetItem, QHeaderView,
        QComboBox, QCheckBox, QWidget, QFrame,
        QSizePolicy, QMessageBox, QGroupBox, QTextEdit,
        QPushButton,
    )
    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtGui import QColor, QBrush, QFont

from pages.base_page import BasePage
from config.machine_config import (
    MachineConfig, MesaConnector, MesaPin,
    ALL_FUNCTION_LABELS, FUNC_TO_TYPE, FUNC_LOOKUP,
    STEPGEN_FUNCTIONS, ENCODER_FUNCTIONS, PWMGEN_FUNCTIONS, SSERIAL_FUNCTIONS,
    get_firmware_spec,
)

# ── Column indices ────────────────────────────────────────────────────────────
COL_PIN    = 0
COL_FUNC   = 1
COL_TYPE   = 2
COL_INVERT = 3
COL_HAL    = 4

COLUMN_HEADERS = ["Pin #", "Function", "Type", "Inv", "HAL Pin"]

PIN_TYPES = ["GPIO", "StepGen", "Encoder", "PWM", "SSerial", "Analog"]

# Colours
CLR_DUPLICATE = QColor("#BF616A")   # red
CLR_ASSIGNED  = QColor("#3B4252")   # dark row tint when not unused
CLR_DEFAULT   = QColor("transparent")


# ─────────────────────────────────────────────────────────────────────────────
# Single connector table
# ─────────────────────────────────────────────────────────────────────────────

class ConnectorTable(QTableWidget):
    """
    One connector's pin assignment table.

    Communicates back to the parent ConnectorsPage via a shared
    'on_change' callable so cross-connector duplicate detection works.
    """

    def __init__(self, connector: MesaConnector, board_name: str,
                 on_change_cb=None, parent=None):
        super().__init__(parent)
        self.connector = connector
        self._board    = board_name
        self._on_change = on_change_cb  # called on any function change
        self._building = False
        self._build()

    def _build(self):
        self._building = True
        self.setColumnCount(5)
        self.setHorizontalHeaderLabels(COLUMN_HEADERS)
        self.setRowCount(len(self.connector.pins))

        hdr = self.horizontalHeader()
        hdr.setSectionResizeMode(COL_PIN,    QHeaderView.ResizeMode.Fixed)
        hdr.setSectionResizeMode(COL_FUNC,   QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(COL_TYPE,   QHeaderView.ResizeMode.Fixed)
        hdr.setSectionResizeMode(COL_INVERT, QHeaderView.ResizeMode.Fixed)
        hdr.setSectionResizeMode(COL_HAL,    QHeaderView.ResizeMode.ResizeToContents)

        self.setColumnWidth(COL_PIN,    48)
        self.setColumnWidth(COL_TYPE,  100)
        self.setColumnWidth(COL_INVERT, 36)

        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.verticalHeader().setVisible(False)
        self.setShowGrid(True)
        self.setWordWrap(False)

        for row, pin in enumerate(self.connector.pins):
            self._populate_row(row, pin)

        self._building = False

    def _populate_row(self, row: int, pin: MesaPin):
        # ── Pin number (read-only) ────────────────────────────────────────
        num_item = QTableWidgetItem(str(pin.num))
        num_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        num_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        num_item.setFont(self._mono_font())
        self.setItem(row, COL_PIN, num_item)

        # ── Function combo ────────────────────────────────────────────────
        func_combo = QComboBox()
        func_combo.addItems(ALL_FUNCTION_LABELS)
        idx = func_combo.findText(pin.function)
        func_combo.setCurrentIndex(max(idx, 0))
        func_combo.currentTextChanged.connect(
            lambda text, r=row: self._on_function_changed(r, text)
        )
        self.setCellWidget(row, COL_FUNC, func_combo)

        # ── Type combo (auto-set but user-editable) ───────────────────────
        type_combo = QComboBox()
        type_combo.addItems(PIN_TYPES)
        idx = type_combo.findText(pin.pin_type)
        type_combo.setCurrentIndex(max(idx, 0))
        self.setCellWidget(row, COL_TYPE, type_combo)

        # ── Invert checkbox ───────────────────────────────────────────────
        cb_widget = QWidget()
        cb_layout = QHBoxLayout(cb_widget)
        cb_layout.setContentsMargins(0, 0, 0, 0)
        cb_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cb = QCheckBox()
        cb.setChecked(pin.invert)
        cb_layout.addWidget(cb)
        self.setCellWidget(row, COL_INVERT, cb_widget)

        # ── HAL pin preview ───────────────────────────────────────────────
        hal_item = QTableWidgetItem(self._resolve_hal(pin.function, pin.num))
        hal_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        hal_item.setFont(self._mono_font())
        hal_item.setForeground(QBrush(QColor("#88C0D0")))
        self.setItem(row, COL_HAL, hal_item)

        self.setRowHeight(row, 28)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _mono_font(self) -> QFont:
        f = QFont("Monospace")
        f.setPointSize(8)
        f.setStyleHint(QFont.StyleHint.Monospace)
        return f

    def _resolve_hal(self, function: str, pin_num: int) -> str:
        tmpl, _ = FUNC_LOOKUP.get(function, ("", ""))
        if not tmpl:
            return ""
        try:
            return tmpl.format(board=self._board, pin=pin_num, n=0)
        except (KeyError, IndexError):
            return tmpl

    def _on_function_changed(self, row: int, text: str):
        if self._building:
            return

        # Auto-set type
        new_type = FUNC_TO_TYPE.get(text, "GPIO")
        type_combo = self.cellWidget(row, COL_TYPE)
        if type_combo:
            idx = type_combo.findText(new_type)
            if idx >= 0:
                type_combo.setCurrentIndex(idx)

        # Update HAL preview
        pin_num = int(self.item(row, COL_PIN).text())
        hal_text = self._resolve_hal(text, pin_num)
        hal_item = self.item(row, COL_HAL)
        if hal_item:
            hal_item.setText(hal_text)

        # Notify parent for cross-table validation
        if self._on_change:
            self._on_change()

    # ── Data extraction ───────────────────────────────────────────────────────

    def get_pins(self) -> List[MesaPin]:
        pins = []
        for row in range(self.rowCount()):
            num_item = self.item(row, COL_PIN)
            num = int(num_item.text()) if num_item else row

            func_combo = self.cellWidget(row, COL_FUNC)
            function = func_combo.currentText() if func_combo else "Unused"

            type_combo = self.cellWidget(row, COL_TYPE)
            pin_type = type_combo.currentText() if type_combo else "GPIO"

            invert = False
            invert_widget = self.cellWidget(row, COL_INVERT)
            if invert_widget:
                for child in invert_widget.children():
                    if isinstance(child, QCheckBox):
                        invert = child.isChecked()
                        break

            hal_item = self.item(row, COL_HAL)
            hal_pin = hal_item.text() if hal_item else ""

            pins.append(MesaPin(
                num=num, function=function, pin_type=pin_type,
                invert=invert, hal_pin=hal_pin
            ))
        return pins

    def highlight_duplicates(self, dup_functions: Set[str]):
        """Colour rows whose function is in the duplicate set."""
        for row in range(self.rowCount()):
            func_combo = self.cellWidget(row, COL_FUNC)
            if func_combo is None:
                continue
            func = func_combo.currentText()
            colour = CLR_DUPLICATE if (func != "Unused" and func in dup_functions) else CLR_DEFAULT
            for col in [COL_PIN, COL_HAL]:
                item = self.item(row, col)
                if item:
                    item.setBackground(QBrush(colour))

    def all_functions(self) -> List[str]:
        result = []
        for row in range(self.rowCount()):
            w = self.cellWidget(row, COL_FUNC)
            result.append(w.currentText() if w else "Unused")
        return result


# ─────────────────────────────────────────────────────────────────────────────
# Main ConnectorsPage
# ─────────────────────────────────────────────────────────────────────────────

class ConnectorsPage(BasePage):
    PAGE_TITLE    = "Mesa Connector Pin Assignment"
    PAGE_SUBTITLE = "Assign functions to each physical pin on Mesa connectors"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tables: Dict[str, ConnectorTable] = {}
        self._cfg: Optional[MachineConfig] = None
        self._build_ui()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(8)

        # Info bar
        info_row = QHBoxLayout()
        info_lbl = QLabel(
            "Assign signal functions to each pin. "
            "Unused pins default to GPIO. "
            "Invert flips the active logic level."
        )
        info_lbl.setWordWrap(True)
        info_lbl.setStyleSheet("color: #81A1C1; font-size: 9pt;")
        info_row.addWidget(info_lbl, 1)

        self._status_lbl = QLabel("")
        self._status_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._status_lbl.setStyleSheet("font-size: 8.5pt;")
        info_row.addWidget(self._status_lbl)
        root.addLayout(info_row)

        # Connector tabs
        self._tab_widget = QTabWidget()
        root.addWidget(self._tab_widget, 1)

        # HAL preview panel
        self._hal_grp = QGroupBox("HAL Net Preview  (read-only)")
        hal_layout = QVBoxLayout(self._hal_grp)
        self._hal_preview = QTextEdit()
        self._hal_preview.setReadOnly(True)
        self._hal_preview.setFont(self._mono_font())
        self._hal_preview.setMaximumHeight(130)
        self._hal_preview.setStyleSheet(
            "background: #1E1E2E; color: #A3BE8C; border: none;"
        )
        btn_row = QHBoxLayout()
        self._refresh_btn = QPushButton("↻  Refresh Preview")
        self._refresh_btn.setFixedWidth(160)
        self._refresh_btn.clicked.connect(self._update_hal_preview)
        btn_row.addWidget(self._refresh_btn)
        btn_row.addStretch()
        hal_layout.addLayout(btn_row)
        hal_layout.addWidget(self._hal_preview)
        root.addWidget(self._hal_grp)

    def _mono_font(self) -> QFont:
        f = QFont("Monospace")
        f.setPointSize(8)
        f.setStyleHint(QFont.StyleHint.Monospace)
        return f

    # ── populate / save ───────────────────────────────────────────────────────

    def populate(self, cfg: MachineConfig):
        self._cfg = cfg
        self._tab_widget.clear()
        self._tables.clear()

        m = cfg.mesa

        # Ensure connectors match firmware
        if not m.connectors:
            m.update_from_firmware()

        board = m.board_name

        for conn in m.connectors:
            table = ConnectorTable(
                connector=conn,
                board_name=board,
                on_change_cb=self._on_any_change,
            )
            self._tables[conn.name] = table
            self._tab_widget.addTab(table, conn.name)

        # Smart Serial info tab
        if m.num_smart_serial > 0:
            ss_widget = self._build_ss_info_tab(m)
            self._tab_widget.addTab(ss_widget, "Smart Serial")

        self._update_status()
        self._update_hal_preview()

    def save(self, cfg: MachineConfig):
        for conn in cfg.mesa.connectors:
            if conn.name in self._tables:
                conn.pins = self._tables[conn.name].get_pins()
        self._update_status()

    # ── validation ────────────────────────────────────────────────────────────

    def validate(self):
        if self._cfg is None:
            return True, ""

        # Collect all non-Unused assignments across all connectors
        all_funcs: Dict[str, str] = {}  # function → "Connector:Pin"
        duplicates: Set[str] = set()

        for conn_name, table in self._tables.items():
            for row in range(table.rowCount()):
                w = table.cellWidget(row, COL_FUNC)
                if w is None:
                    continue
                func = w.currentText()
                if func == "Unused":
                    continue
                pin_num = int(table.item(row, COL_PIN).text())
                loc = f"{conn_name}:{pin_num}"
                if func in all_funcs:
                    duplicates.add(func)
                else:
                    all_funcs[func] = loc

        # Highlight duplicates
        for table in self._tables.values():
            table.highlight_duplicates(duplicates)

        if duplicates:
            dup_list = "\n".join(f"  • {f}" for f in sorted(duplicates))
            return False, f"Duplicate pin assignments detected:\n{dup_list}"

        # Check stepgen count vs configured count
        m = self._cfg.mesa
        sg_used = {
            f for f in all_funcs if f in STEPGEN_FUNCTIONS
        }
        # Extract unique stepgen channel indices
        sg_nums: Set[int] = set()
        for f in sg_used:
            try:
                sg_nums.add(int(f.split("-")[1].split()[0]))
            except (ValueError, IndexError):
                pass

        if len(sg_nums) > m.num_stepgens:
            return False, (
                f"StepGen channels assigned ({len(sg_nums)}) exceeds "
                f"configured count ({m.num_stepgens}). "
                f"Increase StepGen count on the Mesa Config page, "
                f"or remove extra assignments."
            )

        spec = get_firmware_spec(m.board_name, m.firmware)
        if spec and len(sg_nums) > spec.max_stepgens:
            return False, (
                f"StepGen channels ({len(sg_nums)}) exceed firmware limit "
                f"({spec.max_stepgens}) for {m.firmware}."
            )

        # Check encoder count
        enc_nums: Set[int] = set()
        for f in all_funcs:
            if f in ENCODER_FUNCTIONS:
                try:
                    enc_nums.add(int(f.split("-")[1].split()[0]))
                except (ValueError, IndexError):
                    pass
        if spec and len(enc_nums) > spec.max_encoders:
            return False, (
                f"Encoder channels ({len(enc_nums)}) exceed firmware limit "
                f"({spec.max_encoders}) for {m.firmware}."
            )

        return True, ""

    # ── helpers ───────────────────────────────────────────────────────────────

    def _on_any_change(self):
        """Called by any ConnectorTable when a function changes."""
        self._update_status()
        # Debounce HAL preview update
        QTimer.singleShot(200, self._update_hal_preview)

    def _update_status(self):
        if self._cfg is None:
            return
        m = self._cfg.mesa

        # Count active assignments
        sg_set: Set[int] = set()
        enc_set: Set[int] = set()
        total_assigned = 0

        for table in self._tables.values():
            for func in table.all_functions():
                if func == "Unused":
                    continue
                total_assigned += 1
                if func in STEPGEN_FUNCTIONS:
                    try:
                        sg_set.add(int(func.split("-")[1].split()[0]))
                    except (ValueError, IndexError):
                        pass
                elif func in ENCODER_FUNCTIONS:
                    try:
                        enc_set.add(int(func.split("-")[1].split()[0]))
                    except (ValueError, IndexError):
                        pass

        spec = get_firmware_spec(m.board_name, m.firmware)
        sg_max  = spec.max_stepgens if spec else m.num_stepgens
        enc_max = spec.max_encoders if spec else m.num_encoders

        sg_colour  = "#BF616A" if len(sg_set) > sg_max else "#A3BE8C"
        enc_colour = "#BF616A" if len(enc_set) > enc_max else "#A3BE8C"

        self._status_lbl.setText(
            f"<span style='color:{sg_colour}'>StepGen: {len(sg_set)}/{sg_max}</span>"
            f"  <span style='color:{enc_colour}'>Encoder: {len(enc_set)}/{enc_max}</span>"
            f"  <span style='color:#4C566A'>Assigned: {total_assigned}</span>"
        )
        self._status_lbl.setTextFormat(Qt.TextFormat.RichText)

    def _update_hal_preview(self):
        """Generate HAL net statements for all non-Unused pins."""
        if self._cfg is None:
            return
        lines = [
            f"# HAL pin preview — {self._cfg.mesa.board_name} / "
            f"{self._cfg.mesa.firmware}",
            "",
        ]
        board = self._cfg.mesa.board_name

        for conn_name, table in self._tables.items():
            has_any = False
            conn_lines = [f"# Connector {conn_name}"]
            for row in range(table.rowCount()):
                func_w = table.cellWidget(row, COL_FUNC)
                if func_w is None:
                    continue
                func = func_w.currentText()
                if func == "Unused":
                    continue
                has_any = True

                pin_num  = int(table.item(row, COL_PIN).text())
                hal_item = table.item(row, COL_HAL)
                hal_pin  = hal_item.text() if hal_item else ""

                # Invert flag
                invert_w = table.cellWidget(row, COL_INVERT)
                invert = False
                if invert_w:
                    for child in invert_w.children():
                        if isinstance(child, QCheckBox):
                            invert = child.isChecked()

                inv_str = " (inverted)" if invert else ""

                # Build net statement
                if "Step" in func:
                    # StepGen nets
                    axis_hint = ["x", "y", "z", "a", "b", "c", "u", "v", "w"]
                    try:
                        sg_n = int(func.split("-")[1].split()[0])
                        ax = axis_hint[sg_n] if sg_n < len(axis_hint) else str(sg_n)
                    except (ValueError, IndexError):
                        ax = "?"
                    sig_type = "step" if "Step" in func else "dir"
                    net_name = f"{ax}-{sig_type}"
                    conn_lines.append(f"net {net_name} => {hal_pin}{inv_str}")
                elif "Encoder" in func or "MPG" in func:
                    try:
                        enc_n = int(func.split("-")[1].split()[0])
                        phase = func.split()[-1].lower() if func.split() else "a"
                        net_name = f"enc{enc_n}-{phase}"
                    except (ValueError, IndexError):
                        net_name = f"encoder-{pin_num}"
                    conn_lines.append(f"net {net_name} <= {hal_pin}{inv_str}")
                elif func in ("GPIO Input", "E-Stop In", "Amp Fault In",
                              "Home X", "Home Y", "Home Z", "Home A",
                              "Limit+ X", "Limit- X", "Limit+ Y",
                              "Limit- Y", "Limit+ Z", "Limit- Z",
                              "Probe In", "MPG A", "MPG B"):
                    sig_map = {
                        "E-Stop In": "estop-in",
                        "Amp Fault In": "amp-fault",
                        "Home X": "home-x", "Home Y": "home-y",
                        "Home Z": "home-z", "Home A": "home-a",
                        "Limit+ X": "limit-pos-x", "Limit- X": "limit-neg-x",
                        "Limit+ Y": "limit-pos-y", "Limit- Y": "limit-neg-y",
                        "Limit+ Z": "limit-pos-z", "Limit- Z": "limit-neg-z",
                        "Probe In": "probe-in",
                        "MPG A": "mpg-a", "MPG B": "mpg-b",
                    }
                    net_name = sig_map.get(func, f"gpio-{pin_num:03d}-in")
                    conn_lines.append(f"net {net_name} <= {hal_pin}{inv_str}")
                else:
                    sig_map_out = {
                        "GPIO Output": f"gpio-{pin_num:03d}-out",
                        "Amp Enable": "amp-enable",
                        "Charge Pump": "charge-pump",
                        "Spindle Out": "spindle-vel-cmd",
                        "Spindle Enable": "spindle-enable",
                        "Spindle Dir": "spindle-dir",
                    }
                    net_name = sig_map_out.get(func, f"sig-{func.lower().replace(' ', '-')}")
                    conn_lines.append(f"net {net_name} => {hal_pin}{inv_str}")

            if has_any:
                lines.extend(conn_lines)
                lines.append("")

        self._hal_preview.setPlainText("\n".join(lines))

    def _build_ss_info_tab(self, m) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(16, 16, 16, 16)
        from config.machine_config import SmartSerialChannel
        title = QLabel(
            f"Smart Serial: {m.num_smart_serial} port(s), "
            f"{m.num_smart_serial_channels} channel(s)/port"
        )
        title.setStyleSheet("font-weight: bold;")
        v.addWidget(title)

        from PyQt6.QtWidgets import QTableWidget as TW, QTableWidgetItem as TWI, QHeaderView as HV
        table = TW(len(m.sserial_channels), 3)
        table.setHorizontalHeaderLabels(["Channel", "Device", "Address"])
        table.horizontalHeader().setSectionResizeMode(1, HV.ResizeMode.Stretch)
        table.setEditTriggers(TW.EditTrigger.NoEditTriggers)
        for i, ch in enumerate(m.sserial_channels):
            table.setItem(i, 0, TWI(f"Port {i // m.num_smart_serial_channels}, "
                                    f"Ch {i % m.num_smart_serial_channels}"))
            table.setItem(i, 1, TWI(ch.device))
            table.setItem(i, 2, TWI(str(ch.device_address)))
        v.addWidget(table)
        v.addStretch()
        return w
