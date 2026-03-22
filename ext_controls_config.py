"""
External Controls — Full Parameter Model
==========================================
Exact parity with original LinuxCNC GTK PnCConf wizard for the
External Controls page.  Every configurable field present in the
GTK wizard has a corresponding attribute here.

HAL mapping notes (used by ExternalControlsHAL in hal_generator):
  VFD     → loadusr <driver>  + spindle signals
  MPG     → loadrt encoder    → halui.axis.X.jog-accel-fraction / jog-vel-mode
  Button  → hal_input / GPIO  → halui.jog.X.plus / minus
  JoyJog  → hal_input (USB)   → halui.jog.X.analog
  FO      → encoder/analog    → halui.feed-override.scale
  MVO     → encoder/analog    → halui.max-velocity.value
  SO      → encoder/analog    → halui.spindle.0.override.scale
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Optional


# ─────────────────────────────────────────────────────────────────────────────
# VFD
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class VFDConfig:
    """
    Serial Variable-Frequency Drive.
    Matches GTK fields: driver, device, baud, stop_bits, parity,
    slave, accel_time, decel_time, spindle_at_speed_tolerance.
    """
    enabled: bool = False

    # Driver selection
    # gs2 | vfs11 | hy_vfd | abb_badvfd | smc_gs2 | spindle-orient
    driver: str = "gs2"

    # Serial port
    device: str = "/dev/ttyS0"
    baud: int = 9600           # 1200|2400|4800|9600|19200|38400|57600|115200
    stop_bits: int = 1         # 1 | 2
    parity: str = "none"       # none | even | odd

    # Modbus slave address
    slave: int = 1             # 1..247

    # Ramp times (seconds)
    accel_time: float = 5.0    # acceleration time
    decel_time: float = 5.0    # deceleration time

    # Spindle-at-speed tolerance (fraction of commanded speed, 0..1)
    spindle_at_speed_tolerance: float = 0.1

    # HAL signal names (auto-derived but user-overridable)
    hal_spindle_speed_in: str  = "spindle.0.speed-out-rps"
    hal_spindle_enable:   str  = "spindle.0.on"
    hal_spindle_fwd:      str  = "spindle.0.forward"
    hal_spindle_rev:      str  = "spindle.0.reverse"

    def hal_loadusr(self, machine_name: str) -> str:
        """Return the loadusr line for this VFD driver."""
        if self.driver == "gs2":
            return (
                f"loadusr -Wn vfd gs2_vfd "
                f"-n vfd "
                f"-d {self.device} "
                f"-r {self.baud} "
                f"-t {self.slave}"
            )
        elif self.driver == "hy_vfd":
            return (
                f"loadusr -Wn vfd hy_vfd "
                f"-n vfd "
                f"-d {self.device} "
                f"-r {self.baud} "
                f"-s {self.slave}"
            )
        elif self.driver == "vfs11":
            return (
                f"loadusr -Wn vfd vfs11_vfd "
                f"-d {self.device} "
                f"-r {self.baud}"
            )
        else:
            return f"# loadusr for {self.driver} — configure manually"


# ─────────────────────────────────────────────────────────────────────────────
# Button Jog
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ButtonJogAxisConfig:
    """Per-axis button jog configuration."""
    enabled: bool = True
    # HAL pin names for the physical buttons (GPIO pin or signal name)
    pin_positive: str = ""   # e.g. "hm2_5i25.0.gpio.001.in"
    pin_negative: str = ""   # e.g. "hm2_5i25.0.gpio.002.in"
    # Invert logic (active-low switches)
    invert_positive: bool = False
    invert_negative: bool = False
    # Jog speed (machine units/min), 0 = use default
    jog_speed: float = 0.0


@dataclass
class ButtonJogConfig:
    """
    External button jogging.
    Per-axis button pairs + a shared slow/fast speed.
    Matches GTK: axis list, per-axis pin assignment, speed inputs.
    """
    enabled: bool = False

    # Axes that have button jog assigned (subset of machine axes)
    axes: Dict[str, ButtonJogAxisConfig] = field(default_factory=lambda: {
        "X": ButtonJogAxisConfig(),
        "Y": ButtonJogAxisConfig(),
        "Z": ButtonJogAxisConfig(),
    })

    # Shared speeds
    slow_speed: float = 100.0   # mm/min (or in/min)
    fast_speed: float = 1000.0

    # Use a separate "fast" button (like a shift key)
    use_fast_button: bool = False
    fast_button_pin: str = ""


# ─────────────────────────────────────────────────────────────────────────────
# MPG (Manual Pulse Generator)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class MPGIncrementRow:
    """
    One row of the MPG increment table.
    Original GTK table columns: a, b, c, d, ab, bc, abc
    where a/b/c/d are switch states and ab/bc/abc are
    derived combinations that select a step size.
    """
    # Switch inputs (True = switch active / closed)
    a: bool = False
    b: bool = False
    c: bool = False
    d: bool = False
    # Combination columns (computed or manually set)
    ab: bool  = False
    bc: bool  = False
    abc: bool = False
    # The increment distance for this row (machine units)
    increment: float = 0.001


def _default_mpg_increments() -> List[MPGIncrementRow]:
    """Default 4-row increment table matching original PnCConf defaults."""
    return [
        MPGIncrementRow(a=False, b=False, c=False, d=False, increment=0.001),
        MPGIncrementRow(a=True,  b=False, c=False, d=False, increment=0.010),
        MPGIncrementRow(a=False, b=True,  c=False, d=False, increment=0.100),
        MPGIncrementRow(a=True,  b=True,  c=False, d=False, increment=1.000),
    ]


@dataclass
class MPGConfig:
    """
    Manual Pulse Generator — the most complex external control.

    Modes (radio-button exclusive):
      use_mpg        — direct quadrature encoder input
      use_switches   — digital inputs select increment + direction
      use_increments — increment table mode (switch combination → step size)

    HAL component: encoder (realtime) or hal_input (userspace for USB MPG).
    """
    enabled: bool = False

    # Mode selection
    mode: str = "use_mpg"   # "use_mpg" | "use_switches" | "use_increments"

    # Encoder / quadrature input pin names
    encoder_a_pin: str = ""
    encoder_b_pin: str = ""
    encoder_index_pin: str = ""   # optional index pulse

    # Axis selection — which axis does the MPG control
    # Empty string = use halui axis-select switches
    mpg_axis: str = ""   # "" | "X" | "Y" | "Z" | "A" | "B" | "C"

    # Velocity / acceleration
    jog_velocity: float = 100.0    # mm/min — max jog speed via MPG
    scale: float = 1.0             # counts-per-unit scaling

    # Increment table (use_increments mode)
    increment_table: List[MPGIncrementRow] = field(
        default_factory=_default_mpg_increments
    )

    # Switch mode: individual digital pins
    switch_pin_a: str = ""
    switch_pin_b: str = ""
    switch_pin_c: str = ""
    switch_pin_d: str = ""

    # Signal conditioning
    debounce_time: float = 0.0     # seconds, 0 = disabled
    use_gray_code: bool = False    # decoder expects Gray-coded switches
    ignore_false_inputs: bool = False  # filter glitches

    # Axis-select switch pins (when mpg_axis is "")
    axis_select_pins: Dict[str, str] = field(default_factory=lambda: {
        "X": "", "Y": "", "Z": "", "A": "",
    })

    @property
    def increment_strings(self) -> str:
        """Space-separated increment list for INI INCREMENTS key."""
        return " ".join(str(r.increment) for r in self.increment_table)


# ─────────────────────────────────────────────────────────────────────────────
# USB / Joystick Jogging
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class JoyJogAxisMapping:
    """Mapping of one joystick axis to a machine axis."""
    machine_axis: str = "X"   # X | Y | Z | A
    joystick_axis: int = 0    # physical joystick axis index
    invert: bool = False
    scale: float = 1.0        # speed scaling factor


@dataclass
class JoyJogConfig:
    """
    USB Joystick jogging via hal_input component.
    Matches GTK: device, deadzone, axis mappings, speed.
    """
    enabled: bool = False

    # Device path
    device: str = "/dev/input/js0"

    # hal_input instance name
    hal_name: str = "joystick"

    # Deadzone (0..1 fraction of full axis range below which input = 0)
    deadzone: float = 0.2

    # Speed scaling: joystick full deflection → this speed (mm/min)
    max_speed: float = 1000.0

    # Axis mappings
    axis_mappings: List[JoyJogAxisMapping] = field(default_factory=lambda: [
        JoyJogAxisMapping(machine_axis="X", joystick_axis=0),
        JoyJogAxisMapping(machine_axis="Y", joystick_axis=1),
        JoyJogAxisMapping(machine_axis="Z", joystick_axis=2),
    ])

    # Button assignments (button index → HAL function)
    # e.g. {0: "estop", 1: "home-all"}
    button_map: Dict[int, str] = field(default_factory=dict)


# ─────────────────────────────────────────────────────────────────────────────
# Override controls (Feed / Max-Vel / Spindle)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class OverrideConfig:
    """
    Generic override control (FO / MVO / SO).
    Input mode: analog (0–10 V), encoder (quadrature), or switch-ladder.
    Matches GTK fields for all three override tabs identically.
    """
    enabled: bool = False

    # Input mode
    mode: str = "encoder"   # "encoder" | "analog" | "switches"

    # Encoder mode
    encoder_a_pin: str = ""
    encoder_b_pin: str = ""
    counts_per_revolution: int = 100   # for absolute % calculation

    # Analog mode
    analog_pin: str = ""
    analog_min_voltage: float = 0.0    # V at 0 % override
    analog_max_voltage: float = 10.0   # V at max override

    # Scaling
    min_value: float = 0.0    # minimum override value (fraction, 0.0 = 0 %)
    max_value: float = 1.5    # maximum override value (1.5 = 150 %)
    scale: float = 1.0        # additional manual scale factor

    # Optional low-pass filter time constant (seconds), 0 = off
    filter_time: float = 0.0

    # Debounce (for switch-ladder mode), seconds
    debounce_time: float = 0.0

    # Switch-ladder mode: list of (pin, value) pairs
    # Each switch adds its value to the override when closed
    switch_ladder: List[Dict] = field(default_factory=list)

    # HAL signal this override drives
    # FO  → "halui.feed-override.scale"
    # MVO → "halui.max-velocity.value"   (or motion.max-velocity)
    # SO  → "halui.spindle.0.override.scale"
    hal_target_pin: str = ""


# ─────────────────────────────────────────────────────────────────────────────
# Top-level External Controls Config
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ExternalControlsConfig:
    """
    Master external controls configuration.
    Each sub-config has its own `enabled` flag that is kept in sync
    with the left-panel checkbox in the UI.
    """
    # Left-panel enable flags (drive checkbox state)
    use_serial_vfd:          bool = False
    use_ext_button_jogging:  bool = False
    use_mpg:                 bool = False
    use_feed_override:       bool = False
    use_max_vel_override:    bool = False
    use_spindle_override:    bool = False
    use_usb_jogging:         bool = False

    # Sub-configs
    vfd:            VFDConfig        = field(default_factory=VFDConfig)
    button_jog:     ButtonJogConfig  = field(default_factory=ButtonJogConfig)
    mpg:            MPGConfig        = field(default_factory=MPGConfig)
    joy_jog:        JoyJogConfig     = field(default_factory=JoyJogConfig)
    feed_override:  OverrideConfig   = field(default_factory=lambda: OverrideConfig(
                                            hal_target_pin="halui.feed-override.scale"))
    max_vel_override: OverrideConfig = field(default_factory=lambda: OverrideConfig(
                                            hal_target_pin="halui.max-velocity.value"))
    spindle_override: OverrideConfig = field(default_factory=lambda: OverrideConfig(
                                            hal_target_pin="halui.spindle.0.override.scale"))

    # Legacy flat fields (backward compat with old config saves)
    use_ext_jogging: bool = False
    mpg_increments:  str  = "0.1 0.01 0.001"

    def sync_enabled_flags(self):
        """Keep sub-config .enabled flags in sync with master flags."""
        self.vfd.enabled            = self.use_serial_vfd
        self.button_jog.enabled     = self.use_ext_button_jogging
        self.mpg.enabled            = self.use_mpg
        self.feed_override.enabled  = self.use_feed_override
        self.max_vel_override.enabled = self.use_max_vel_override
        self.spindle_override.enabled = self.use_spindle_override
        self.joy_jog.enabled        = self.use_usb_jogging
        # legacy
        self.use_ext_jogging        = self.use_ext_button_jogging
        self.mpg_increments         = self.mpg.increment_strings
