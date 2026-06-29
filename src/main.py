#!/usr/bin/env python3
"""
PNCconf Qt Wizard - Main Entry Point
LinuxCNC Mesa card configuration wizard built with PyQt6/PySide6.
"""

import sys
import os

# Prefer PyQt6, fall back to PySide6
try:
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QFontDatabase, QFont
    PYQT6 = True
except ImportError:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QFontDatabase, QFont
    PYQT6 = False

from wizard_controller import WizardController
from ui_theme.stylesheet import DARK_INDUSTRIAL_STYLESHEET


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("PNCconf Qt Wizard")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("LinuxCNC")

    # Apply global stylesheet
    app.setStyleSheet(DARK_INDUSTRIAL_STYLESHEET)

    # Set default font
    font = QFont("Roboto", 10)
    font.setStyleHint(QFont.StyleHint.SansSerif)
    app.setFont(font)

    # Launch wizard
    wizard = WizardController()
    wizard.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
