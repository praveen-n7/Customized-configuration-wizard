"""Mesa Connector Pin Assignment Page"""
from __future__ import annotations
from typing import List

try:
    from PyQt6.QtWidgets import (
        QVBoxLayout, QHBoxLayout, QLabel, QTabWidget,
        QTableWidget, QTableWidgetItem, QHeaderView,
        QComboBox, QCheckBox, QWidget, QFrame,
    )
    from PyQt6.QtCore import Qt, QSize
    from PyQt6.QtGui import QColor
except ImportError:
    from PySide6.QtWidgets import (
        QVBoxLayout, QHBoxLayout, QLabel, QTabWidget,
        QTableWidget, QTableWidgetItem, QHeaderView,
        QComboBox, QCheckBox, QWidget, QFrame,
    )
    from PySide6.QtCore import Qt, QSize
    from PySide6.QtGui import QColor

from pages.base_page import BasePage
from config.machine_config import MachineConfig, MesaConnector, MesaPin


PIN_FUNCTIONS = [
    "Unused",
    "StepGen Step",
    "StepGen Dir",
    "StepGen Step/Dir",
    "Encoder A",
    "Encoder B",
    "Encoder Z",
    "PWM",
    "GPIO In",
    "GPIO Out",
    "UART TX",
    "UART RX",
    "Smart Serial TX",
    "Smart Serial RX",
    "Spinout",
    "Spinena",
    "Spindir",
    "E-Stop In",
    "E-Stop Out",
    "Amp Enable",
    "Amp Fault",
    "Home/Limit",
    "Probe",
    "Charge Pump",
]

PIN_TYPES = ["GPIO", "StepGen", "Encoder", "PWM", "SSerial", "Analog"]

COLUMN_HEADERS = ["Pin #", "Function", "Type", "Invert"]
COL_NUM, COL_FUNC, COL_TYPE, COL_INVERT = 0, 1, 2, 3


class ConnectorTable(QTableWidget):
    """A single connector's pin assignment table."""

    def __init__(self, connector: MesaConnector, parent=None):
        super().__init__(parent)
        self.connector = connector
        self._build()

    def _build(self):
        self.setColumnCount(4)
        self.setHorizontalHeaderLabels(COLUMN_HEADERS)
        self.setRowCount(len(self.connector.pins))

        header = self.horizontalHeader()
        header.setSectionResizeMode(COL_NUM,    QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(COL_FUNC,   QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(COL_TYPE,   QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(COL_INVERT, QHeaderView.ResizeMode.Fixed)
        self.setColumnWidth(COL_NUM,    60)
        self.setColumnWidth(COL_TYPE,  110)
        self.setColumnWidth(COL_INVERT, 70)

        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.verticalHeader().setVisible(False)
        self.setShowGrid(True)

        for row, pin in enumerate(self.connector.pins):
            self._populate_row(row, pin)

    def _populate_row(self, row: int, pin: MesaPin):
        # Pin number (read-only)
        num_item = QTableWidgetItem(str(pin.num))
        num_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        num_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        self.setItem(row, COL_NUM, num_item)

        # Function combo
        func_combo = QComboBox()
        func_combo.addItems(PIN_FUNCTIONS)
        idx = func_combo.findText(pin.function)
        if idx >= 0:
            func_combo.setCurrentIndex(idx)
        func_combo.currentTextChanged.connect(
            lambda text, r=row: self._on_function_changed(r, text)
        )
        self.setCellWidget(row, COL_FUNC, func_combo)

        # Type combo
        type_combo = QComboBox()
        type_combo.addItems(PIN_TYPES)
        idx = type_combo.findText(pin.pin_type)
        if idx >= 0:
            type_combo.setCurrentIndex(idx)
        self.setCellWidget(row, COL_TYPE, type_combo)

        # Invert checkbox (centered)
        cb_widget = QWidget()
        cb_layout = QHBoxLayout(cb_widget)
        cb_layout.setContentsMargins(0, 0, 0, 0)
        cb_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cb = QCheckBox()
        cb.setChecked(pin.invert)
        cb_layout.addWidget(cb)
        self.setCellWidget(row, COL_INVERT, cb_widget)

        self.setRowHeight(row, 32)

    def _on_function_changed(self, row: int, text: str):
        # Auto-set pin type based on function name
        type_map = {
            "StepGen": "StepGen",
            "Encoder": "Encoder",
            "PWM": "PWM",
            "Smart Serial": "SSerial",
            "UART": "GPIO",
            "GPIO": "GPIO",
            "Unused": "GPIO",
        }
        type_combo = self.cellWidget(row, COL_TYPE)
        if type_combo:
            for key, typ in type_map.items():
                if key in text:
                    idx = type_combo.findText(typ)
                    if idx >= 0:
                        type_combo.setCurrentIndex(idx)
                    break

    def get_pins(self) -> List[MesaPin]:
        pins = []
        for row in range(self.rowCount()):
            num_item = self.item(row, COL_NUM)
            num = int(num_item.text()) if num_item else row

            func_combo = self.cellWidget(row, COL_FUNC)
            function = func_combo.currentText() if func_combo else "Unused"

            type_combo = self.cellWidget(row, COL_TYPE)
            pin_type = type_combo.currentText() if type_combo else "GPIO"

            # Invert: cellWidget is a container
            invert_widget = self.cellWidget(row, COL_INVERT)
            invert = False
            if invert_widget:
                for child in invert_widget.children():
                    if isinstance(child, QCheckBox):
                        invert = child.isChecked()
                        break

            pins.append(MesaPin(num=num, function=function, pin_type=pin_type, invert=invert))
        return pins


class ConnectorsPage(BasePage):
    PAGE_TITLE = "Mesa Connector Pin Assignment"
    PAGE_SUBTITLE = "Assign functions to each physical pin on Mesa connectors"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tables: dict[str, ConnectorTable] = {}
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 16, 24, 16)
        root.setSpacing(12)

        info = QLabel(
            "Assign signal functions to each pin. Unused pins default to GPIO. "
            "Invert flips the active logic level."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #81A1C1; font-size: 9pt;")
        root.addWidget(info)

        self._tabs = QTabWidget()
        root.addWidget(self._tabs)

    def populate(self, cfg: MachineConfig):
        self._tabs.clear()
        self._tables.clear()

        connectors = cfg.mesa.connectors
        if not connectors:
            connectors = [MesaConnector("P2"), MesaConnector("P3")]

        for conn in connectors:
            table = ConnectorTable(conn)
            self._tables[conn.name] = table
            self._tabs.addTab(table, conn.name)

        # Smart Serial tab
        if cfg.mesa.num_smart_serial > 0:
            ss_widget = QWidget()
            ss_layout = QVBoxLayout(ss_widget)
            ss_layout.addWidget(QLabel(
                f"{cfg.mesa.num_smart_serial} Smart Serial port(s) configured.\n"
                "Smart Serial device assignment is done in the 7i76 I/O page."
            ))
            self._tabs.addTab(ss_widget, "Smart Serial")

    def save(self, cfg: MachineConfig):
        for conn in cfg.mesa.connectors:
            if conn.name in self._tables:
                conn.pins = self._tables[conn.name].get_pins()
