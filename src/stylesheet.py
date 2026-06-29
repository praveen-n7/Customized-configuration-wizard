"""
Dark Industrial Theme Stylesheet for PNCconf Qt Wizard.
Consistent modern UI matching LinuxCNC industrial aesthetic.
"""

DARK_INDUSTRIAL_STYLESHEET = """
/* =========================================================
   ROOT / WINDOW
   ========================================================= */
QMainWindow, QWidget {
    background-color: #1E1E2E;
    color: #ECEFF4;
    font-family: "Roboto", "Segoe UI", sans-serif;
    font-size: 10pt;
}

/* =========================================================
   PANELS / FRAMES / GROUP BOXES
   ========================================================= */
QFrame#pagePanel, QFrame.panel {
    background-color: #2A2A3C;
    border-radius: 8px;
    border: 1px solid #3A3A50;
}

QGroupBox {
    background-color: #2A2A3C;
    border: 1px solid #3A3A50;
    border-radius: 6px;
    margin-top: 14px;
    padding-top: 10px;
    font-weight: 600;
    color: #A0C4E8;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    left: 10px;
    top: 2px;
    color: #5E81AC;
    font-size: 9pt;
    font-weight: 700;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}

/* =========================================================
   SIDEBAR / NAV PANEL
   ========================================================= */
QFrame#sidebarFrame {
    background-color: #16162A;
    border-right: 1px solid #3A3A50;
}

QLabel#sidebarTitle {
    color: #5E81AC;
    font-size: 13pt;
    font-weight: 700;
    padding: 16px 16px 8px 16px;
    letter-spacing: 1px;
}

QLabel#sidebarVersion {
    color: #4C566A;
    font-size: 8pt;
    padding: 0 16px 16px 16px;
}

/* Step list in sidebar */
QListWidget#stepList {
    background-color: transparent;
    border: none;
    outline: none;
    padding: 4px 0;
}

QListWidget#stepList::item {
    padding: 8px 16px;
    color: #4C566A;
    border-left: 3px solid transparent;
    font-size: 9pt;
}

QListWidget#stepList::item:selected {
    background-color: #2A2A3C;
    color: #ECEFF4;
    border-left: 3px solid #5E81AC;
}

QListWidget#stepList::item[completed="true"] {
    color: #A3BE8C;
}

/* =========================================================
   HEADER BAR
   ========================================================= */
QFrame#headerFrame {
    background-color: #2A2A3C;
    border-bottom: 1px solid #3A3A50;
    min-height: 64px;
    max-height: 64px;
}

QLabel#pageTitle {
    font-size: 15pt;
    font-weight: 700;
    color: #ECEFF4;
    padding-left: 8px;
}

QLabel#pageSubtitle {
    font-size: 9pt;
    color: #81A1C1;
    padding-left: 8px;
}

/* =========================================================
   BUTTONS
   ========================================================= */
QPushButton {
    background-color: #3A3A50;
    color: #ECEFF4;
    border: none;
    border-radius: 6px;
    padding: 8px 20px;
    font-size: 10pt;
    font-weight: 500;
    min-width: 88px;
    min-height: 34px;
}

QPushButton:hover {
    background-color: #4A4A65;
}

QPushButton:pressed {
    background-color: #2A2A3C;
}

QPushButton:disabled {
    background-color: #252535;
    color: #4C566A;
}

QPushButton#btnNext, QPushButton#btnFinish {
    background-color: #5E81AC;
    color: #ECEFF4;
    font-weight: 600;
}

QPushButton#btnNext:hover, QPushButton#btnFinish:hover {
    background-color: #81A1C1;
}

QPushButton#btnNext:pressed, QPushButton#btnFinish:pressed {
    background-color: #4C6F9A;
}

QPushButton#btnBack {
    background-color: transparent;
    border: 1px solid #3A3A50;
    color: #81A1C1;
}

QPushButton#btnBack:hover {
    background-color: #2A2A3C;
    border-color: #5E81AC;
}

QPushButton.danger {
    background-color: #BF616A;
}

QPushButton.danger:hover {
    background-color: #D08770;
}

QPushButton.success {
    background-color: #A3BE8C;
    color: #1E1E2E;
}

/* =========================================================
   LINE EDITS / SPIN BOXES / COMBO BOXES
   ========================================================= */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #16162A;
    border: 1px solid #3A3A50;
    border-radius: 5px;
    color: #ECEFF4;
    padding: 6px 10px;
    min-height: 28px;
    selection-background-color: #5E81AC;
}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
    border: 1px solid #5E81AC;
    background-color: #1A1A2E;
}

QLineEdit:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled {
    color: #4C566A;
    background-color: #1A1A2A;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #81A1C1;
    margin-right: 6px;
}

QComboBox QAbstractItemView {
    background-color: #2A2A3C;
    border: 1px solid #5E81AC;
    selection-background-color: #5E81AC;
    color: #ECEFF4;
    outline: none;
}

QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
    background-color: #3A3A50;
    border: none;
    width: 16px;
    border-radius: 3px;
}

QSpinBox::up-button:hover, QSpinBox::down-button:hover,
QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {
    background-color: #5E81AC;
}

/* =========================================================
   CHECKBOXES / RADIO BUTTONS
   ========================================================= */
QCheckBox, QRadioButton {
    color: #ECEFF4;
    spacing: 8px;
}

QCheckBox::indicator, QRadioButton::indicator {
    width: 16px;
    height: 16px;
}

QCheckBox::indicator {
    border: 1px solid #3A3A50;
    border-radius: 3px;
    background-color: #16162A;
}

QCheckBox::indicator:checked {
    background-color: #5E81AC;
    border-color: #5E81AC;
    image: none;
}

QCheckBox::indicator:checked:after {
    content: "";
}

QRadioButton::indicator {
    border: 1px solid #3A3A50;
    border-radius: 8px;
    background-color: #16162A;
}

QRadioButton::indicator:checked {
    background-color: #5E81AC;
    border-color: #5E81AC;
}

/* =========================================================
   TABLES
   ========================================================= */
QTableWidget, QTableView {
    background-color: #16162A;
    border: 1px solid #3A3A50;
    border-radius: 6px;
    gridline-color: #2A2A3C;
    color: #ECEFF4;
    outline: none;
    alternate-background-color: #1A1A2A;
}

QTableWidget::item, QTableView::item {
    padding: 6px 10px;
    border: none;
}

QTableWidget::item:selected, QTableView::item:selected {
    background-color: #3A4A60;
    color: #ECEFF4;
}

QHeaderView::section {
    background-color: #2A2A3C;
    color: #81A1C1;
    padding: 8px 10px;
    border: none;
    border-right: 1px solid #3A3A50;
    border-bottom: 1px solid #3A3A50;
    font-weight: 600;
    font-size: 9pt;
    letter-spacing: 0.3px;
}

QHeaderView::section:first {
    border-radius: 6px 0 0 0;
}

/* =========================================================
   TAB WIDGET
   ========================================================= */
QTabWidget::pane {
    background-color: #2A2A3C;
    border: 1px solid #3A3A50;
    border-radius: 0 6px 6px 6px;
}

QTabBar::tab {
    background-color: #1E1E2E;
    color: #4C566A;
    padding: 8px 18px;
    border: 1px solid #3A3A50;
    border-bottom: none;
    border-radius: 6px 6px 0 0;
    margin-right: 2px;
    font-size: 9pt;
}

QTabBar::tab:selected {
    background-color: #2A2A3C;
    color: #ECEFF4;
    border-color: #5E81AC;
    font-weight: 600;
}

QTabBar::tab:hover:!selected {
    background-color: #252538;
    color: #81A1C1;
}

/* =========================================================
   SCROLL BARS
   ========================================================= */
QScrollBar:vertical {
    background-color: #1E1E2E;
    width: 8px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background-color: #3A3A50;
    border-radius: 4px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #5E81AC;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar:horizontal {
    background-color: #1E1E2E;
    height: 8px;
    border-radius: 4px;
}

QScrollBar::handle:horizontal {
    background-color: #3A3A50;
    border-radius: 4px;
    min-width: 20px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #5E81AC;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}

/* =========================================================
   LABELS
   ========================================================= */
QLabel {
    color: #ECEFF4;
}

QLabel.hint {
    color: #4C566A;
    font-size: 8.5pt;
    font-style: italic;
}

QLabel.value-display {
    color: #A3BE8C;
    font-family: "Courier New", monospace;
    font-size: 9.5pt;
}

QLabel.section-header {
    color: #5E81AC;
    font-size: 10pt;
    font-weight: 700;
    letter-spacing: 0.5px;
    padding-bottom: 4px;
    border-bottom: 1px solid #3A3A50;
}

QLabel.warning {
    color: #EBCB8B;
}

QLabel.error {
    color: #BF616A;
}

/* =========================================================
   PROGRESS / STATUS BAR
   ========================================================= */
QProgressBar {
    background-color: #16162A;
    border: 1px solid #3A3A50;
    border-radius: 4px;
    height: 6px;
    text-align: center;
    color: transparent;
}

QProgressBar::chunk {
    background-color: #5E81AC;
    border-radius: 4px;
}

QStatusBar {
    background-color: #16162A;
    color: #4C566A;
    border-top: 1px solid #3A3A50;
    font-size: 8.5pt;
}

/* =========================================================
   TOOL TIPS
   ========================================================= */
QToolTip {
    background-color: #2A2A3C;
    color: #ECEFF4;
    border: 1px solid #5E81AC;
    border-radius: 4px;
    padding: 6px 10px;
    font-size: 9pt;
}

/* =========================================================
   SEPARATORS
   ========================================================= */
QFrame[frameShape="4"],  /* HLine */
QFrame[frameShape="5"] { /* VLine */
    color: #3A3A50;
    background-color: #3A3A50;
    max-height: 1px;
}

/* =========================================================
   TEXT EDIT (summary/log areas)
   ========================================================= */
QTextEdit, QPlainTextEdit {
    background-color: #16162A;
    border: 1px solid #3A3A50;
    border-radius: 6px;
    color: #A3BE8C;
    font-family: "Courier New", monospace;
    font-size: 9pt;
    padding: 8px;
    selection-background-color: #5E81AC;
}
"""
