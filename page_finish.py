"""
Finish / Generate Page
======================
- Shows full configuration summary
- Prompts for output folder (with default pre-filled)
- Generates all files on Finish button click:
    <machine_name>.hal
    custom.hal
    <machine_name>.ini
    pncconf.json  (project save)
- Opens the output folder in the file manager after writing
- Preview pane shows generated content with tab selector
"""
from __future__ import annotations
import os
import subprocess
import sys

try:
    from PyQt6.QtWidgets import (
        QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
        QPushButton, QGroupBox, QFrame, QFileDialog,
        QLineEdit, QTabWidget, QWidget, QMessageBox,
        QSizePolicy, QScrollArea,
    )
    from PyQt6.QtCore import Qt, QThread, pyqtSignal as Signal
    from PyQt6.QtGui import QFont, QColor
except ImportError:
    from PySide6.QtWidgets import (
        QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
        QPushButton, QGroupBox, QFrame, QFileDialog,
        QLineEdit, QTabWidget, QWidget, QMessageBox,
        QSizePolicy, QScrollArea,
    )
    from PySide6.QtCore import Qt, QThread, Signal
    from PySide6.QtGui import QFont, QColor

from pages.base_page import BasePage
from config.machine_config import MachineConfig
from hal_generator.hal_gen import HALGenerator
from hal_generator.ini_gen import INIGenerator


# ─────────────────────────────────────────────────────────────────────────────
# Background generation worker (keeps UI responsive)
# ─────────────────────────────────────────────────────────────────────────────

class _GenerateWorker(QThread):
    progress   = Signal(str)          # status messages
    finished   = Signal(bool, str)    # (success, message)

    def __init__(self, cfg: MachineConfig, out_dir: str):
        super().__init__()
        self._cfg     = cfg
        self._out_dir = out_dir

    def run(self):
        try:
            os.makedirs(self._out_dir, exist_ok=True)

            self.progress.emit("Generating HAL file…")
            hal_gen  = HALGenerator(self._cfg)
            hal_gen.write_all(self._out_dir)

            self.progress.emit("Generating INI file…")
            ini_gen  = INIGenerator(self._cfg)
            ini_gen.write(self._out_dir)

            self.progress.emit("Saving project (pncconf.json)…")
            json_path = os.path.join(
                self._out_dir, "pncconf.json")
            self._cfg.save(json_path)

            # Create empty .pref file named after the machine/config.
            # Overwrites safely if it already exists.
            pref_path = os.path.join(
                self._out_dir, f"{self._cfg.machine_name}.pref")
            open(pref_path, "w").close()

            self.progress.emit("Done.")
            self.finished.emit(True, self._out_dir)

        except Exception as e:
            self.finished.emit(False, str(e))


# ─────────────────────────────────────────────────────────────────────────────
# Finish Page
# ─────────────────────────────────────────────────────────────────────────────

class FinishPage(BasePage):
    PAGE_TITLE    = "Finish"
    PAGE_SUBTITLE = "Review configuration, choose output folder, and generate LinuxCNC files"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cfg: MachineConfig | None = None
        self._worker: _GenerateWorker | None = None
        self._build_ui()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        root = QVBoxLayout(container)
        root.setContentsMargins(28, 20, 28, 20)
        root.setSpacing(14)

        # ── Summary ───────────────────────────────────────────────────────────
        sum_grp = QGroupBox("Configuration Summary")
        sum_l   = QVBoxLayout(sum_grp)
        self._summary_text = QTextEdit()
        self._summary_text.setReadOnly(True)
        self._summary_text.setFont(self._mono(9))
        self._summary_text.setMinimumHeight(200)
        self._summary_text.setMaximumHeight(260)
        sum_l.addWidget(self._summary_text)
        root.addWidget(sum_grp)

        # ── Output Directory ──────────────────────────────────────────────────
        dir_grp = QGroupBox("Output Folder")
        dir_l   = QVBoxLayout(dir_grp)

        dir_hint = QLabel(
            "All generated files will be saved here.  "
            "LinuxCNC reads configs from  ~/linuxcnc/configs/<machine_name>/")
        dir_hint.setWordWrap(True)
        dir_hint.setStyleSheet("color:#81A1C1; font-size:8.5pt;")
        dir_l.addWidget(dir_hint)

        path_row = QHBoxLayout()
        self._dir_edit = QLineEdit()
        self._dir_edit.setPlaceholderText(
            "Click 'Browse…' or type a path, e.g.  "
            "/home/user/linuxcnc/configs/my_machine")
        self._dir_edit.setFont(self._mono(9))
        self._dir_edit.setStyleSheet("color:#A3BE8C;")
        self._dir_edit.textChanged.connect(self._on_dir_changed)

        self._browse_btn = QPushButton("Browse…")
        self._browse_btn.setFixedWidth(90)
        self._browse_btn.clicked.connect(self._browse_dir)

        self._open_btn = QPushButton("Open Folder")
        self._open_btn.setFixedWidth(110)
        self._open_btn.setToolTip("Open output folder in file manager")
        self._open_btn.clicked.connect(self._open_folder)
        self._open_btn.setEnabled(False)

        path_row.addWidget(self._dir_edit, 1)
        path_row.addWidget(self._browse_btn)
        path_row.addWidget(self._open_btn)
        dir_l.addLayout(path_row)

        # Files that will be created
        self._files_lbl = QLabel("")
        self._files_lbl.setStyleSheet(
            "color:#4C566A; font-size:8pt; font-family:monospace;")
        self._files_lbl.setWordWrap(True)
        dir_l.addWidget(self._files_lbl)
        root.addWidget(dir_grp)

        # ── Generate buttons ──────────────────────────────────────────────────
        gen_grp = QGroupBox("Generate Files")
        gen_l   = QVBoxLayout(gen_grp)

        btn_row = QHBoxLayout()

        self._btn_preview_hal = QPushButton("Preview HAL")
        self._btn_preview_hal.clicked.connect(self._preview_hal)
        self._btn_preview_hal.setFixedWidth(120)

        self._btn_preview_ini = QPushButton("Preview INI")
        self._btn_preview_ini.clicked.connect(self._preview_ini)
        self._btn_preview_ini.setFixedWidth(120)

        self._btn_gen_all = QPushButton("💾  Generate & Save All Files")
        self._btn_gen_all.setObjectName("btnFinish")
        self._btn_gen_all.setMinimumHeight(42)
        self._btn_gen_all.setMinimumWidth(220)
        self._btn_gen_all.clicked.connect(self._generate_all)

        btn_row.addWidget(self._btn_preview_hal)
        btn_row.addWidget(self._btn_preview_ini)
        btn_row.addStretch()
        btn_row.addWidget(self._btn_gen_all)
        gen_l.addLayout(btn_row)

        # Status line
        self._status_lbl = QLabel("")
        self._status_lbl.setWordWrap(True)
        self._status_lbl.setStyleSheet("font-size:9pt;")
        gen_l.addWidget(self._status_lbl)
        root.addWidget(gen_grp)

        # ── Preview pane ──────────────────────────────────────────────────────
        prev_grp = QGroupBox("File Preview")
        prev_l   = QVBoxLayout(prev_grp)

        tab_row = QHBoxLayout()
        self._prev_tabs = QTabWidget()
        self._prev_tabs.setTabPosition(QTabWidget.TabPosition.North)

        self._hal_preview  = self._make_preview_edit()
        self._ini_preview  = self._make_preview_edit()
        self._cust_preview = self._make_preview_edit()
        self._json_preview = self._make_preview_edit()

        self._prev_tabs.addTab(self._hal_preview,  "machine.hal")
        self._prev_tabs.addTab(self._ini_preview,  "machine.ini")
        self._prev_tabs.addTab(self._cust_preview, "custom.hal")
        self._prev_tabs.addTab(self._json_preview, "pncconf.json")

        prev_l.addWidget(self._prev_tabs)
        root.addWidget(prev_grp)

        scroll.setWidget(container)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _mono(pt: int = 9) -> QFont:
        f = QFont("Courier New")
        f.setPointSize(pt)
        f.setStyleHint(QFont.StyleHint.Monospace)
        return f

    def _make_preview_edit(self) -> QTextEdit:
        t = QTextEdit()
        t.setReadOnly(True)
        t.setFont(self._mono(8))
        t.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        t.setMinimumHeight(200)
        t.setStyleSheet(
            "background:#111120; color:#ECEFF4; "
            "border:1px solid #3A3A50;")
        t.setPlaceholderText("Click 'Preview HAL' or 'Preview INI' to populate…")
        return t

    def _set_status(self, msg: str, ok: bool = True):
        color = "#A3BE8C" if ok else "#BF616A"
        self._status_lbl.setText(msg)
        self._status_lbl.setStyleSheet(
            f"color:{color}; font-size:9pt;")

    def _update_files_label(self, out_dir: str, name: str):
        if out_dir:
            self._files_lbl.setText(
                f"Files to be written:\n"
                f"  {os.path.join(out_dir, name + '.hal')}\n"
                f"  {os.path.join(out_dir, name + '.ini')}\n"
                f"  {os.path.join(out_dir, 'custom.hal')}\n"
                f"  {os.path.join(out_dir, 'pncconf.json')}")
        else:
            self._files_lbl.setText("")

    # ── Directory handling ────────────────────────────────────────────────────

    def _browse_dir(self):
        start = self._dir_edit.text() or os.path.expanduser(
            f"~/linuxcnc/configs/{self._cfg.machine_name if self._cfg else 'my_machine'}")
        path = QFileDialog.getExistingDirectory(
            self, "Select Output Folder", start)
        if path:
            self._dir_edit.setText(path)

    def _on_dir_changed(self, text: str):
        if self._cfg:
            self._cfg.config_directory = text.strip()
            self._update_files_label(
                text.strip(), self._cfg.machine_name)

    def _open_folder(self):
        path = self._dir_edit.text().strip()
        if not path or not os.path.isdir(path):
            self._set_status("Folder does not exist yet — generate files first.", ok=False)
            return
        try:
            if sys.platform.startswith("linux"):
                subprocess.Popen(["xdg-open", path])
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                os.startfile(path)
        except Exception as e:
            self._set_status(f"Could not open folder: {e}", ok=False)

    # ── Summary builder ───────────────────────────────────────────────────────

    def _build_summary(self, cfg: MachineConfig) -> str:
        sep = "─" * 54
        lines = [
            "╔" + "═" * 54 + "╗",
            "║  FPGA CONFIGURATION WIZARD  —  SUMMARY" + " " * 14 + "║",
            "╚" + "═" * 54 + "╝",
            "",
            f"  Operator         : meukron  (Belagavi, KA)",
            f"  Machine Name     : {cfg.machine_name}",
            f"  Config Directory : {cfg.config_directory or '(not set)'}",
            f"  Axis Config      : {cfg.axis_config}",
            f"  Units            : {cfg.units}",
            f"  Servo Period     : {cfg.servo_period_ns:,} ns  "
            f"({cfg.servo_period_ns / 1_000_000:.3f} ms)",
            "",
            sep,
            "  MESA FPGA",
            sep,
            f"  Board            : {cfg.mesa.board_name}",
            f"  Firmware         : {cfg.mesa.firmware}",
            f"  Card Address     : {getattr(cfg.mesa, 'ip_address', 'N/A')}",
            f"  Encoders         : {cfg.mesa.num_encoders}",
            f"  Step Generators  : {cfg.mesa.num_stepgens}",
            f"  PWM Generators   : {cfg.mesa.num_pwmgens}",
            f"  Smart Serial     : {cfg.mesa.num_smart_serial} port(s)",
            f"  PWM Frequency    : {cfg.mesa.pwm_base_freq:,} Hz",
            f"  Watchdog         : {cfg.mesa.watchdog_timeout} ms",
            "",
            sep,
            "  AXES",
            sep,
        ]

        for letter in cfg.axis_config:
            ax = cfg.axes.get(letter)
            if ax:
                lines += [
                    f"  Axis {letter}:",
                    f"    Travel         : {ax.travel:.3f} {cfg.units[:2]}",
                    f"    Max Velocity   : {ax.max_velocity:.3f} {cfg.units[:2]}/s",
                    f"    Max Accel      : {ax.max_acceleration:.3f} {cfg.units[:2]}/s²",
                    f"    Scale          : {ax.scale:.4f} steps/unit",
                    f"    Following Err  : {ax.ferror:.4f} / {ax.min_ferror:.5f}",
                    f"    Home Position  : {ax.home_position:.4f}",
                    f"    Search Vel     : {ax.search_velocity:.4f}",
                    "",
                ]

        lines += [
            sep,
            "  SPINDLE",
            sep,
            f"  Speed Range      : {cfg.spindle.min_rpm:.0f} – "
            f"{cfg.spindle.max_rpm:.0f} RPM",
            f"  Encoder Feedback : {'Yes' if cfg.spindle.use_encoder else 'No'}",
            f"  At-Speed Signal  : {'Yes' if cfg.spindle.spindle_at_speed else 'No'}",
            "",
            sep,
            "  OPTIONS",
            sep,
            f"  GUI              : {cfg.screen.gui_type}",
            f"  PyVCP            : {'Yes' if cfg.vcp.include_pyvcp else 'No'}",
            f"  GladeVCP         : {'Yes' if cfg.vcp.include_gladevcp else 'No'}",
            f"  ClassicLadder    : {'Yes' if cfg.options.use_classicladder else 'No'}",
            f"  HALUI Commands   : {len(cfg.options.halui_commands)}",
            "",
        ]
        return "\n".join(lines)

    # ── Preview ───────────────────────────────────────────────────────────────

    def _preview_hal(self):
        if not self._cfg:
            return
        try:
            text = HALGenerator(self._cfg).generate_machine_hal()
            self._hal_preview.setPlainText(text)
            cust = HALGenerator(self._cfg).generate_custom_hal()
            self._cust_preview.setPlainText(cust)
            self._prev_tabs.setCurrentIndex(0)
            self._set_status("HAL preview ready.", ok=True)
        except Exception as e:
            self._set_status(f"HAL preview error: {e}", ok=False)

    def _preview_ini(self):
        if not self._cfg:
            return
        try:
            text = INIGenerator(self._cfg).generate()
            self._ini_preview.setPlainText(text)
            self._prev_tabs.setCurrentIndex(1)
            self._set_status("INI preview ready.", ok=True)
        except Exception as e:
            self._set_status(f"INI preview error: {e}", ok=False)

    # ── Generate all ──────────────────────────────────────────────────────────

    def _generate_all(self):
        if not self._cfg:
            self._set_status("No configuration loaded.", ok=False)
            return

        out_dir = self._dir_edit.text().strip()

        # ── Prompt for directory if not set ──────────────────────────────────
        if not out_dir:
            default = os.path.expanduser(
                f"~/linuxcnc/configs/{self._cfg.machine_name}")
            out_dir = QFileDialog.getExistingDirectory(
                self,
                "Choose Output Folder for Generated Files",
                os.path.dirname(default),
            )
            if not out_dir:
                # User cancelled — offer to create the default
                reply = QMessageBox.question(
                    self,
                    "No Folder Selected",
                    f"No folder was selected.\n\n"
                    f"Create and use the default folder?\n"
                    f"{default}",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                if reply == QMessageBox.StandardButton.Yes:
                    out_dir = default
                else:
                    self._set_status(
                        "Generation cancelled — select an output folder first.",
                        ok=False)
                    return
            self._dir_edit.setText(out_dir)

        # ── Confirm overwrite if directory already has files ──────────────────
        if os.path.isdir(out_dir):
            existing = [
                f for f in os.listdir(out_dir)
                if f.endswith((".hal", ".ini", ".json"))
            ]
            if existing:
                reply = QMessageBox.question(
                    self,
                    "Overwrite Existing Files?",
                    f"The folder already contains {len(existing)} "
                    f"config file(s):\n"
                    f"  {out_dir}\n\n"
                    "Overwrite with new generated files?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return

        # ── Disable button during generation ─────────────────────────────────
        self._btn_gen_all.setEnabled(False)
        self._btn_gen_all.setText("⏳  Generating…")
        self._set_status("Starting file generation…", ok=True)

        # ── Run in background thread ──────────────────────────────────────────
        self._worker = _GenerateWorker(self._cfg, out_dir)
        self._worker.progress.connect(
            lambda msg: self._set_status(msg, ok=True))
        self._worker.finished.connect(self._on_generation_done)
        self._worker.start()

    def _on_generation_done(self, success: bool, result: str):
        self._btn_gen_all.setEnabled(True)
        self._btn_gen_all.setText("💾  Generate & Save All Files")

        if success:
            out_dir = result
            self._cfg.config_directory = out_dir
            self._open_btn.setEnabled(True)

            # Auto-populate previews
            try:
                hal_file = os.path.join(
                    out_dir, f"{self._cfg.machine_name}.hal")
                ini_file = os.path.join(
                    out_dir, f"{self._cfg.machine_name}.ini")
                cust_file = os.path.join(out_dir, "custom.hal")
                json_file = os.path.join(out_dir, "pncconf.json")

                if os.path.exists(hal_file):
                    self._hal_preview.setPlainText(
                        open(hal_file).read())
                if os.path.exists(ini_file):
                    self._ini_preview.setPlainText(
                        open(ini_file).read())
                if os.path.exists(cust_file):
                    self._cust_preview.setPlainText(
                        open(cust_file).read())
                if os.path.exists(json_file):
                    self._json_preview.setPlainText(
                        open(json_file).read())
            except Exception:
                pass

            name = self._cfg.machine_name
            files_written = "\n".join([
                f"    ✔  {name}.hal",
                f"    ✔  {name}.ini",
                f"    ✔  custom.hal",
                f"    ✔  pncconf.json",
            ])
            self._set_status(
                f"✔  All files saved to:\n"
                f"   {out_dir}\n\n"
                f"{files_written}", ok=True)

            # Offer to open the folder
            reply = QMessageBox.information(
                self,
                "Files Generated Successfully",
                f"All LinuxCNC configuration files have been written to:\n\n"
                f"{out_dir}\n\n"
                f"  •  {name}.hal\n"
                f"  •  {name}.ini\n"
                f"  •  custom.hal\n"
                f"  •  pncconf.json\n\n"
                "Open the output folder now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._open_folder()
        else:
            self._set_status(
                f"✗  Generation failed:\n   {result}", ok=False)
            QMessageBox.critical(
                self, "Generation Failed",
                f"File generation failed with the following error:\n\n{result}")

    # ── Populate / Save ───────────────────────────────────────────────────────

    def populate(self, cfg: MachineConfig):
        self._cfg = cfg

        # Build summary
        self._summary_text.setPlainText(self._build_summary(cfg))

        # Pre-fill output directory from config
        out_dir = cfg.config_directory or os.path.expanduser(
            f"~/linuxcnc/configs/{cfg.machine_name}")
        self._dir_edit.setText(out_dir)
        self._update_files_label(out_dir, cfg.machine_name)

        # Enable Open Folder if directory already exists
        self._open_btn.setEnabled(os.path.isdir(out_dir))

        # Auto-generate previews
        self._preview_hal()
        self._preview_ini()

    def save(self, cfg: MachineConfig):
        cfg.config_directory = self._dir_edit.text().strip()
