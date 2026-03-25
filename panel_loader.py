"""
panel_loader.py
===============
Runtime helper: reads PANEL_NAME / PANEL_PATH from the LinuxCNC INI file
and loads the correct custom GUI control panel.

Usage (called from your launch script or POSTGUI_HALFILE handler):

    from panel_loader import load_panel_from_ini
    load_panel_from_ini("/path/to/machine.ini")

If no panel is configured the function returns None silently — no crash,
no side-effects.  The rest of the machine startup continues normally.

Design constraints
------------------
* No JSON / databases / external storage — INI file is the sole source.
* Does NOT touch HAL or any other existing configuration.
* Safe to call even when [DISPLAY] has no PANEL_NAME / PANEL_PATH keys.
"""

from __future__ import annotations

import configparser
import importlib.util
import os
import subprocess
import sys
from typing import Optional


def _read_ini(ini_path: str) -> configparser.ConfigParser:
    """Return a ConfigParser loaded from *ini_path*."""
    cfg = configparser.ConfigParser(strict=False)
    cfg.read(ini_path)
    return cfg


def get_panel_config(ini_path: str) -> tuple[str, str]:
    """Return (panel_name, panel_path) from the INI file.

    Returns ("", "") when the keys are absent or blank — caller treats
    that as "no panel configured".
    """
    cfg = _read_ini(ini_path)
    panel_name = cfg.get("DISPLAY", "PANEL_NAME", fallback="").strip()
    panel_path = cfg.get("DISPLAY", "PANEL_PATH", fallback="").strip()
    return panel_name, panel_path


def load_panel_from_ini(ini_path: str) -> Optional[str]:
    """Read the INI and launch the configured panel.

    Dispatch logic
    ──────────────
    1.  If PANEL_PATH is a **directory** — run qtvcp with that path as the
        panel name argument, identical to the standard
        ``qtvcp <panel_name>`` invocation LinuxCNC uses.
    2.  If PANEL_PATH ends in ``.ui`` — launch via qtvcp directly.
    3.  If PANEL_PATH ends in ``.py`` — import and call its ``main()``
        (or ``start()`` / ``run()`` if ``main`` is absent), so the panel
        controls its own startup.
    4.  For any other extension — attempt a generic subprocess launch.
        The system logs a warning but does NOT raise an exception.

    Returns the resolved panel_path on success, or None when no panel is
    configured (safe fallback).
    """
    panel_name, panel_path = get_panel_config(ini_path)

    if not panel_name or not panel_path:
        # No panel configured — silent fallback, nothing to do.
        return None

    if not os.path.exists(panel_path):
        _warn(
            f"panel_loader: PANEL_PATH '{panel_path}' does not exist. "
            "Skipping panel load."
        )
        return None

    _info(f"panel_loader: loading panel '{panel_name}' from '{panel_path}'")

    try:
        if os.path.isdir(panel_path):
            _launch_qtvcp_panel(panel_name, panel_path)

        elif panel_path.endswith(".ui"):
            _launch_qtvcp_ui(panel_name, panel_path)

        elif panel_path.endswith(".py"):
            _launch_python_panel(panel_path)

        else:
            _launch_subprocess(panel_path)

    except Exception as exc:  # noqa: BLE001
        # Never crash the machine startup — log and continue.
        _warn(f"panel_loader: failed to load panel '{panel_name}': {exc}")
        return None

    return panel_path


# ─────────────────────────────────────────────────────────────────────────────
# Private launchers
# ─────────────────────────────────────────────────────────────────────────────

def _launch_qtvcp_panel(panel_name: str, panel_dir: str) -> None:
    """Launch qtvcp with the given panel directory as its working directory."""
    cmd = ["qtvcp", panel_name]
    _info(f"panel_loader: exec {cmd!r}  (cwd={panel_dir})")
    subprocess.Popen(cmd, cwd=panel_dir)


def _launch_qtvcp_ui(panel_name: str, ui_path: str) -> None:
    """Launch qtvcp pointing directly at a .ui file."""
    cmd = ["qtvcp", ui_path]
    _info(f"panel_loader: exec {cmd!r}")
    subprocess.Popen(cmd)


def _launch_python_panel(py_path: str) -> None:
    """Import a .py panel module and call its entry-point."""
    spec = importlib.util.spec_from_file_location("_panel_module", py_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from '{py_path}'")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]

    # Try common entry-point names in order of preference.
    for entry in ("main", "start", "run"):
        fn = getattr(module, entry, None)
        if callable(fn):
            _info(f"panel_loader: calling {py_path}:{entry}()")
            fn()
            return

    _warn(
        f"panel_loader: '{py_path}' has no main()/start()/run() — "
        "module imported but no entry-point called."
    )


def _launch_subprocess(path: str) -> None:
    """Generic fallback: execute the path as a subprocess."""
    _info(f"panel_loader: subprocess.Popen({path!r})")
    subprocess.Popen([path])


# ─────────────────────────────────────────────────────────────────────────────
# Logging helpers (avoid hard dependency on logging module at import time)
# ─────────────────────────────────────────────────────────────────────────────

def _info(msg: str) -> None:
    print(msg, file=sys.stdout, flush=True)


def _warn(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)
