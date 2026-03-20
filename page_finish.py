"""Finish / Summary Page"""
from __future__ import annotations
import os

try:
    from PyQt6.QtWidgets import (
        QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
        QPushButton, QGroupBox, QFrame, QFileDialog,
        QProgressBar,
    )
    from PyQt6.QtCore import Qt, QThread, pyqtSignal as Signal
    from PyQt6.QtGui import QColor
except ImportError:
    from PySide6.QtWidgets import (
        QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
        QPushButton, QGroupBox, QFrame, QFileDialog,
        QProgressBar,
    )
    from PySide6.QtCore import Qt, QThread, Signal
    from PySide6.QtGui import QColor

from pages.base_page import BasePage
from config.machine_config import MachineConfig
from hal_generator.hal_gen import HALGenerator
from hal_generator.ini_gen import INIGenerator


class FinishPage(BasePage):
    PAGE_TITLE = "Finish"
    PAGE_SUBTITLE = "Review your configuration and generate LinuxCNC files"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cfg: MachineConfig | None = None
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 24, 32, 24)
        root.setSpacing(16)

        # ── Summary ───────────────────────────────────────────────────────────
        summary_group = QGroupBox("Configuration Summary")
        summary_layout = QVBoxLayout(summary_group)
        self._summary_text = QTextEdit()
        self._summary_text.setReadOnly(True)
        self._summary_text.setMinimumHeight(220)
        summary_layout.addWidget(self._summary_text)
        root.addWidget(summary_group)

        # ── Output Directory ──────────────────────────────────────────────────
        dir_group = QGroupBox("Output Directory")
        dir_layout = QHBoxLayout(dir_group)
        self._output_dir = QLabel("(not set)")
        self._output_dir.setStyleSheet("color: #A3BE8C; font-family: monospace;")
        change_btn = QPushButton("Change…")
        change_btn.setFixedWidth(90)
        change_btn.clicked.connect(self._change_output_dir)
        dir_layout.addWidget(self._output_dir, 1)
        dir_layout.addWidget(change_btn)
        root.addWidget(dir_group)

        # ── Action Buttons ────────────────────────────────────────────────────
        action_group = QGroupBox("Generate Files")
        action_layout = QVBoxLayout(action_group)

        btn_row = QHBoxLayout()

        self._btn_gen_ini = QPushButton("⚙  Generate INI")
        self._btn_gen_ini.setObjectName("btnNext")
        self._btn_gen_hal = QPushButton("⚡  Generate HAL")
        self._btn_gen_hal.setObjectName("btnNext")
        self._btn_gen_all = QPushButton("✓  Generate All Files")
        self._btn_gen_all.setObjectName("btnFinish")
        self._btn_gen_all.setMinimumHeight(40)

        self._btn_gen_ini.clicked.connect(self._generate_ini)
        self._btn_gen_hal.clicked.connect(self._generate_hal)
        self._btn_gen_all.clicked.connect(self._generate_all)

        btn_row.addWidget(self._btn_gen_ini)
        btn_row.addWidget(self._btn_gen_hal)
        btn_row.addStretch()
        btn_row.addWidget(self._btn_gen_all)

        action_layout.addLayout(btn_row)

        self._status_label = QLabel("")
        self._status_label.setWordWrap(True)
        action_layout.addWidget(self._status_label)

        root.addWidget(action_group)

        # ── Preview Tabs would go here in a full implementation ────────────────
        preview_group = QGroupBox("Generated File Preview")
        preview_layout = QVBoxLayout(preview_group)

        self._preview_text = QTextEdit()
        self._preview_text.setReadOnly(True)
        self._preview_text.setMinimumHeight(140)
        self._preview_text.setPlaceholderText("Generated file content will appear here…")
        preview_layout.addWidget(self._preview_text)

        root.addWidget(preview_group)

    def _change_output_dir(self):
        path = QFileDialog.getExistingDirectory(
            self, "Select Output Directory", os.path.expanduser("~")
        )
        if path and self._cfg:
            self._cfg.config_directory = path
            self._output_dir.setText(path)

    def _build_summary(self, cfg: MachineConfig) -> str:
        lines = [
            f"{'═' * 52}",
            f"  CONFIGURATION SUMMARY",
            f"{'═' * 52}",
            f"",
            f"  Machine Name     : {cfg.machine_name}",
            f"  Config Dir       : {cfg.config_directory}",
            f"  Axis Config      : {cfg.axis_config}",
            f"  Units            : {cfg.units}",
            f"  Servo Period     : {cfg.servo_period_ns} ns  "
            f"({cfg.servo_period_ns / 1_000_000:.3f} ms)",
            f"",
            f"  Mesa Board       : {cfg.mesa.board_name}",
            f"  Firmware         : {cfg.mesa.firmware}",
            f"  Encoders         : {cfg.mesa.num_encoders}",
            f"  Step Generators  : {cfg.mesa.num_stepgens}",
            f"  PWM Freq         : {cfg.mesa.pwm_base_freq} Hz",
            f"",
            f"  GUI Frontend     : {cfg.screen.gui_type}",
            f"  Max Feed Ovr     : {cfg.screen.max_feed_override:.0%}",
            f"",
        ]

        lines.append("  Axes:")
        for letter in cfg.axis_config:
            ax = cfg.axes.get(letter)
            if ax:
                lines.append(
                    f"    {letter}  travel={ax.travel:.1f}mm  "
                    f"vel={ax.max_velocity:.1f}mm/s  "
                    f"accel={ax.max_acceleration:.1f}mm/s²  "
                    f"scale={ax.scale:.2f}"
                )

        lines += [
            f"",
            f"  Spindle          : {cfg.spindle.min_rpm:.0f}–{cfg.spindle.max_rpm:.0f} RPM",
            f"  Encoder          : {'Yes' if cfg.spindle.use_encoder else 'No'}",
            f"",
            f"  PyVCP            : {'Yes' if cfg.vcp.include_pyvcp else 'No'}",
            f"  GladeVCP         : {'Yes' if cfg.vcp.include_gladevcp else 'No'}",
            f"  ClassicLadder    : {'Yes' if cfg.options.use_classicladder else 'No'}",
            f"{'═' * 52}",
        ]
        return "\n".join(lines)

    def populate(self, cfg: MachineConfig):
        self._cfg = cfg
        self._summary_text.setPlainText(self._build_summary(cfg))
        self._output_dir.setText(cfg.config_directory or "(not set)")

    def save(self, cfg: MachineConfig):
        pass  # Nothing to save on finish page

    def _generate_ini(self):
        if not self._cfg:
            return
        try:
            gen = INIGenerator(self._cfg)
            content = gen.generate()
            self._preview_text.setPlainText(content)
            self._set_status("✓  INI preview generated.", success=True)
        except Exception as e:
            self._set_status(f"✗  Error: {e}", success=False)

    def _generate_hal(self):
        if not self._cfg:
            return
        try:
            gen = HALGenerator(self._cfg)
            content = gen.generate_machine_hal()
            self._preview_text.setPlainText(content)
            self._set_status("✓  HAL preview generated.", success=True)
        except Exception as e:
            self._set_status(f"✗  Error: {e}", success=False)

    def _generate_all(self):
        if not self._cfg:
            return
        out_dir = self._cfg.config_directory
        if not out_dir:
            self._set_status("✗  Set an output directory first.", success=False)
            return
        try:
            os.makedirs(out_dir, exist_ok=True)
            HALGenerator(self._cfg).write_all(out_dir)
            ini_path = INIGenerator(self._cfg).write(out_dir)
            self._cfg.save(os.path.join(out_dir, "pncconf.json"))
            self._set_status(
                f"✓  All files written to:\n   {out_dir}", success=True
            )
            # Show INI in preview
            with open(ini_path) as f:
                self._preview_text.setPlainText(f.read())
        except Exception as e:
            self._set_status(f"✗  Generation failed: {e}", success=False)

    def _set_status(self, msg: str, success: bool = True):
        color = "#A3BE8C" if success else "#BF616A"
        self._status_label.setText(msg)
        self._status_label.setStyleSheet(f"color: {color}; font-size: 9.5pt;")
