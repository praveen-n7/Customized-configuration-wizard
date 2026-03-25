"""
WizardController
================
Central QMainWindow that orchestrates the PNCconf Qt Wizard.

Responsibilities:
  - Builds the outer chrome: sidebar, header, page area, nav buttons
  - Owns the QStackedWidget with all page instances
  - Drives forward/back navigation with validation
  - Maintains the single MachineConfig instance
  - Syncs sidebar step indicator to current page
  - Emits populate/save calls to each page on entry/exit
"""

from __future__ import annotations
from typing import List, Tuple

try:
    from PyQt6.QtWidgets import (
        QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
        QStackedWidget, QLabel, QPushButton, QListWidget,
        QListWidgetItem, QFrame, QSizePolicy, QMessageBox,
        QProgressBar, QStatusBar, QSplitter,
    )
    from PyQt6.QtCore import Qt, QSize, pyqtSignal as Signal
    from PyQt6.QtGui import QFont, QIcon
except ImportError:
    from PySide6.QtWidgets import (
        QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
        QStackedWidget, QLabel, QPushButton, QListWidget,
        QListWidgetItem, QFrame, QSizePolicy, QMessageBox,
        QProgressBar, QStatusBar, QSplitter,
    )
    from PySide6.QtCore import Qt, QSize, Signal
    from PySide6.QtGui import QFont, QIcon

from config.machine_config import MachineConfig
from pages import (
    BasePage, WelcomePage, ConfigTypePage, BaseMachineInfoPage,
    ScreenConfigPage, VCPPage, ExternalControlsPage, MesaConfigPage,
    ConnectorsPage, IO7i76Page, MotorConfigPage, AxisScalePage,
    AxisConfigPage, SpindleConfigPage, OptionsPage, RealtimePage,
    StepGenAssignPage, EncoderAssignPage, GPIOAssignPage,
    SmartSerialConfigPage, SanityCheckPage, HALPreviewPage,
    FinishPage,
)


# ─────────────────────────────────────────────────────────────────────────────
# Step descriptor
# ─────────────────────────────────────────────────────────────────────────────

class WizardStep:
    def __init__(self, label: str, page: BasePage, group: str = ""):
        self.label = label
        self.page = page
        self.group = group          # sidebar group heading
        self.completed = False


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar step list
# ─────────────────────────────────────────────────────────────────────────────

class SidebarStepList(QListWidget):
    """Read-only navigation list showing all wizard steps."""

    STEP_STYLE = """
        QListWidget {
            background: transparent;
            border: none;
            outline: none;
        }
        QListWidget::item {
            padding: 7px 12px 7px 20px;
            color: #4C566A;
            border-left: 3px solid transparent;
            font-size: 9pt;
        }
        QListWidget::item:selected {
            background: rgba(94, 129, 172, 0.15);
            color: #ECEFF4;
            border-left: 3px solid #5E81AC;
        }
        QListWidget::item[completed="true"] {
            color: #A3BE8C;
        }
        QListWidget::item.group-header {
            color: #5E81AC;
            font-size: 8pt;
            font-weight: 700;
            padding: 10px 12px 2px 12px;
            border-left: none;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(self.STEP_STYLE)
        self.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    def set_current_step(self, index: int):
        for i in range(self.count()):
            item = self.item(i)
            item.setSelected(i == index)

    def mark_completed(self, index: int):
        item = self.item(index)
        if item:
            item.setForeground(__import__(
                "PyQt6.QtGui" if "PyQt6" in __import__("sys").modules else
                "PySide6.QtGui", fromlist=["QColor"]
            ).QColor("#A3BE8C"))


# ─────────────────────────────────────────────────────────────────────────────
# Header bar
# ─────────────────────────────────────────────────────────────────────────────

class HeaderBar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("headerFrame")
        self.setFixedHeight(68)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 8, 24, 8)
        layout.setSpacing(2)

        self._title = QLabel("Welcome")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setWeight(QFont.Weight.Bold)
        self._title.setFont(title_font)
        self._title.setObjectName("pageTitle")

        self._subtitle = QLabel("")
        self._subtitle.setObjectName("pageSubtitle")

        layout.addWidget(self._title)
        layout.addWidget(self._subtitle)

    def update(self, title: str, subtitle: str = ""):
        self._title.setText(title)
        self._subtitle.setText(subtitle)
        self._subtitle.setVisible(bool(subtitle))


# ─────────────────────────────────────────────────────────────────────────────
# Navigation button bar
# ─────────────────────────────────────────────────────────────────────────────

class NavBar(QFrame):
    back_clicked = Signal()
    next_clicked = Signal()
    finish_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(60)
        self.setStyleSheet(
            "background-color: #16162A; border-top: 1px solid #3A3A50;"
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 10, 24, 10)
        layout.setSpacing(10)

        self._progress = QProgressBar()
        self._progress.setFixedHeight(4)
        self._progress.setTextVisible(False)
        self._progress.setRange(0, 100)
        self._progress.setValue(0)

        self._step_label = QLabel("Step 1 of 16")
        self._step_label.setStyleSheet("color: #4C566A; font-size: 8.5pt;")
        self._step_label.setFixedWidth(90)

        self._btn_back = QPushButton("← Back")
        self._btn_back.setObjectName("btnBack")
        self._btn_back.setFixedWidth(100)
        self._btn_back.clicked.connect(self.back_clicked)

        self._btn_next = QPushButton("Next →")
        self._btn_next.setObjectName("btnNext")
        self._btn_next.setFixedWidth(110)
        self._btn_next.clicked.connect(self.next_clicked)

        self._btn_finish = QPushButton("✓  Finish")
        self._btn_finish.setObjectName("btnFinish")
        self._btn_finish.setFixedWidth(110)
        self._btn_finish.setVisible(False)
        self._btn_finish.clicked.connect(self.finish_clicked)

        layout.addWidget(self._step_label)
        layout.addWidget(self._progress, 1)
        layout.addStretch()
        layout.addWidget(self._btn_back)
        layout.addWidget(self._btn_next)
        layout.addWidget(self._btn_finish)

    def update_state(self, current: int, total: int):
        self._step_label.setText(f"Step {current + 1} of {total}")
        pct = int((current / max(total - 1, 1)) * 100)
        self._progress.setValue(pct)
        self._btn_back.setEnabled(current > 0)
        is_last = current == total - 1
        self._btn_next.setVisible(not is_last)
        self._btn_finish.setVisible(is_last)


# ─────────────────────────────────────────────────────────────────────────────
# Main WizardController window
# ─────────────────────────────────────────────────────────────────────────────

class WizardController(QMainWindow):
    """
    Main application window.

    Layout:
    ┌────────────────────────────────────────────────┐
    │  Sidebar (220px)  │  Header (68px)             │
    │                   ├────────────────────────────┤
    │   Step List       │  QStackedWidget (pages)    │
    │                   │                            │
    │                   ├────────────────────────────┤
    │                   │  NavBar (60px)             │
    └────────────────────────────────────────────────┘
    """

    SIDEBAR_WIDTH = 220

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("FPGA Configuration Wizard — meukron  |  LinuxCNC Mesa")
        self.resize(1100, 740)
        self.setMinimumSize(860, 600)

        # Shared config model
        self._cfg = MachineConfig()

        # Build step list
        self._steps: List[WizardStep] = []
        self._current_index = 0

        self._init_pages()
        self._build_chrome()
        self._connect_signals()
        self._go_to(0)

    # ─────────────────────────────────────────────────────────────────────────
    # Page registration
    # ─────────────────────────────────────────────────────────────────────────

    def _init_pages(self):
        """Instantiate all pages and register them as wizard steps."""
        defs: List[Tuple[str, BasePage, str]] = [
            ("Welcome",                 WelcomePage(),          ""),
            ("Configuration Type",      ConfigTypePage(),       "Setup"),
            ("Base Machine Info",        BaseMachineInfoPage(),  "Setup"),
            ("Screen Configuration",    ScreenConfigPage(),     "Display"),
            ("Virtual Control Panel",   VCPPage(),              "Display"),
            ("External Controls",       ExternalControlsPage(), "I/O"),
            ("FPGA Configuration",      MesaConfigPage(),       "Hardware"),
            ("Connector Pin Assign",    ConnectorsPage(),       "Hardware"),
            ("7i76 I/O Config",         IO7i76Page(),           "Hardware"),
            ("Motor Configuration",     MotorConfigPage(),      "Motion"),
            ("Axis Scale Calculation",  AxisScalePage(),        "Motion"),
            ("Axis Configuration",      AxisConfigPage(),       "Motion"),
            ("Spindle Configuration",   SpindleConfigPage(),    "Motion"),
            ("StepGen Assignment",      StepGenAssignPage(),    "FPGA Mapping"),
            ("Encoder Assignment",      EncoderAssignPage(),    "FPGA Mapping"),
            ("GPIO Assignment",         GPIOAssignPage(),       "FPGA Mapping"),
            ("Smart Serial Config",     SmartSerialConfigPage(),"FPGA Mapping"),
            ("Options",                 OptionsPage(),          "Advanced"),
            ("Realtime Components",     RealtimePage(),         "Advanced"),
            ("Sanity Check",            SanityCheckPage(),      "Validation"),
            ("HAL Preview",             HALPreviewPage(),       "Validation"),
            ("Finish",                  FinishPage(),           ""),
        ]

        for label, page, group in defs:
            self._steps.append(WizardStep(label, page, group))

    # ─────────────────────────────────────────────────────────────────────────
    # UI construction
    # ─────────────────────────────────────────────────────────────────────────

    def _build_chrome(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Sidebar ───────────────────────────────────────────────────────────
        sidebar = self._build_sidebar()
        root.addWidget(sidebar)

        # ── Right area: header + stack + navbar ───────────────────────────────
        right_col = QWidget()
        right_layout = QVBoxLayout(right_col)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        self._header = HeaderBar()
        right_layout.addWidget(self._header)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #3A3A50; background: #3A3A50; max-height: 1px;")
        right_layout.addWidget(sep)

        # Page area
        self._stack = QStackedWidget()
        for step in self._steps:
            self._stack.addWidget(step.page)
        right_layout.addWidget(self._stack, 1)

        # Nav bar
        self._navbar = NavBar()
        right_layout.addWidget(self._navbar)

        root.addWidget(right_col, 1)

        # Status bar
        self.statusBar().showMessage("Ready")
        self.statusBar().setStyleSheet(
            "QStatusBar { background: #16162A; color: #4C566A; "
            "border-top: 1px solid #2A2A3C; font-size: 8.5pt; }"
        )

    def _build_sidebar(self) -> QWidget:
        sidebar = QFrame()
        sidebar.setObjectName("sidebarFrame")
        sidebar.setFixedWidth(self.SIDEBAR_WIDTH)
        sidebar.setStyleSheet(
            "QFrame#sidebarFrame {"
            "  background-color: #16162A;"
            "  border-right: 1px solid #3A3A50;"
            "}"
        )

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Logo / title area
        logo_area = QFrame()
        logo_area.setFixedHeight(80)
        logo_area.setStyleSheet("background-color: #12122A; border-bottom: 1px solid #3A3A50;")
        logo_layout = QVBoxLayout(logo_area)
        logo_layout.setContentsMargins(16, 12, 16, 12)
        logo_layout.setSpacing(2)

        title_lbl = QLabel("⚙ FPGA Wizard")
        title_font = QFont()
        title_font.setPointSize(13)
        title_font.setWeight(QFont.Weight.Bold)
        title_lbl.setFont(title_font)
        title_lbl.setStyleSheet("color: #5E81AC;")

        # ── Operator / machine owner badge ────────────────────────────────
        self._operator_lbl = QLabel("👤  meukron")
        self._operator_lbl.setStyleSheet(
            "color: #A3BE8C;"
            "font-size: 9pt;"
            "font-weight: 700;"
            "letter-spacing: 0.5px;"
        )

        ver_lbl = QLabel("Qt Wizard  v1.0  |  Belagavi, KA")
        ver_lbl.setStyleSheet("color: #4C566A; font-size: 7.5pt;")

        logo_area.setFixedHeight(95)          # slightly taller for 3 lines
        logo_layout.addWidget(title_lbl)
        logo_layout.addWidget(self._operator_lbl)
        logo_layout.addWidget(ver_lbl)
        layout.addWidget(logo_area)

        # Step list
        self._sidebar_list = SidebarStepList()
        self._populate_sidebar_list()
        layout.addWidget(self._sidebar_list, 1)

        # Bottom info
        bottom_area = QFrame()
        bottom_area.setFixedHeight(44)
        bottom_area.setStyleSheet("border-top: 1px solid #3A3A50;")
        bottom_layout = QVBoxLayout(bottom_area)
        bottom_layout.setContentsMargins(16, 8, 16, 8)
        bottom_lbl = QLabel("meukron  |  LinuxCNC 2.9+  |  Mesa FPGA")
        bottom_lbl.setStyleSheet(
            "color: #4C566A; font-size: 7.5pt; font-weight: 600;"
        )
        bottom_layout.addWidget(bottom_lbl)
        layout.addWidget(bottom_area)

        return sidebar

    def _populate_sidebar_list(self):
        """Build the sidebar list with optional group headers."""
        self._sidebar_step_row: List[int] = []  # maps step index → list row
        last_group = None

        for step in self._steps:
            if step.group and step.group != last_group:
                # Insert group header item
                header_item = QListWidgetItem(f"  {step.group.upper()}")
                header_item.setFlags(Qt.ItemFlag.NoItemFlags)
                header_item.setForeground(
                    __import__(
                        "PyQt6.QtGui" if "PyQt6" in __import__("sys").modules
                        else "PySide6.QtGui",
                        fromlist=["QColor"]
                    ).QColor("#5E81AC")
                )
                header_font = QFont()
                header_font.setPointSize(7)
                header_font.setWeight(QFont.Weight.Bold)
                header_item.setFont(header_font)
                self._sidebar_list.addItem(header_item)
                last_group = step.group

            step_item = QListWidgetItem(f"  {step.label}")
            step_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self._sidebar_step_row.append(self._sidebar_list.count())
            self._sidebar_list.addItem(step_item)

        # Color first item (welcome) as selected immediately
        self._sidebar_list.item(0).setSelected(True)

    # ─────────────────────────────────────────────────────────────────────────
    # Signal connections
    # ─────────────────────────────────────────────────────────────────────────

    def _connect_signals(self):
        self._navbar.back_clicked.connect(self._go_back)
        self._navbar.next_clicked.connect(self._go_next)
        self._navbar.finish_clicked.connect(self._finish)

    # ─────────────────────────────────────────────────────────────────────────
    # Navigation
    # ─────────────────────────────────────────────────────────────────────────

    def _go_to(self, index: int):
        """Navigate to step by index, calling save on current and populate on new."""
        if not (0 <= index < len(self._steps)):
            return

        # Save current page before leaving
        if self._steps:
            current_page = self._steps[self._current_index].page
            current_page.save(self._cfg)

        self._current_index = index
        step = self._steps[index]

        # Populate new page
        step.page.populate(self._cfg)

        # Switch stack
        self._stack.setCurrentWidget(step.page)

        # Update chrome
        self._header.update(step.page.PAGE_TITLE, step.page.PAGE_SUBTITLE)
        self._navbar.update_state(index, len(self._steps))

        # Update sidebar highlight
        self._sync_sidebar(index)

        # Status bar
        self.statusBar().showMessage(
            f"Step {index + 1} of {len(self._steps)}  —  {step.label}"
        )

    def _go_next(self):
        current_page = self._steps[self._current_index].page

        # Validate
        valid, msg = current_page.validate()
        if not valid:
            QMessageBox.warning(self, "Validation Error", msg)
            return

        # Save
        current_page.save(self._cfg)

        # Mark completed
        self._steps[self._current_index].completed = True
        self._mark_sidebar_completed(self._current_index)

        # Advance
        next_idx = self._current_index + 1
        if next_idx < len(self._steps):
            self._go_to(next_idx)

    def _go_back(self):
        if self._current_index > 0:
            # Save current without validation
            self._steps[self._current_index].page.save(self._cfg)
            self._go_to(self._current_index - 1)

    def _finish(self):
        """Called when the Finish button is pressed on the last page."""
        current_page = self._steps[self._current_index].page
        current_page.save(self._cfg)
        # Delegate to FinishPage which owns the folder picker + file writer
        if hasattr(current_page, "_generate_all"):
            current_page._generate_all()
        else:
            self.statusBar().showMessage(
                "Configuration complete. Use the Generate buttons to save files."
            )

    # ─────────────────────────────────────────────────────────────────────────
    # Sidebar sync helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _sync_sidebar(self, step_index: int):
        """Highlight the correct item in the sidebar list."""
        # Deselect all
        for i in range(self._sidebar_list.count()):
            item = self._sidebar_list.item(i)
            item.setSelected(False)

        # Select the correct step row
        if step_index < len(self._sidebar_step_row):
            row = self._sidebar_step_row[step_index]
            item = self._sidebar_list.item(row)
            if item:
                item.setSelected(True)
                self._sidebar_list.scrollToItem(item)

    def _mark_sidebar_completed(self, step_index: int):
        """Colour a completed step green in the sidebar."""
        if step_index < len(self._sidebar_step_row):
            row = self._sidebar_step_row[step_index]
            item = self._sidebar_list.item(row)
            if item:
                try:
                    from PyQt6.QtGui import QColor
                except ImportError:
                    from PySide6.QtGui import QColor
                item.setForeground(QColor("#A3BE8C"))

    # ─────────────────────────────────────────────────────────────────────────
    # Public API (usable by pages via navigate_to signal if needed)
    # ─────────────────────────────────────────────────────────────────────────

    @property
    def config(self) -> MachineConfig:
        return self._cfg

    def jump_to_step(self, index: int):
        """Allow pages to navigate to a specific step (e.g. from a link)."""
        self._go_to(index)
