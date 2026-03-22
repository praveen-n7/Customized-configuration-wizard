"""
PNCconf Data Model — Full Feature Parity
=========================================
Extended dataclass-based configuration store matching all parameters
available in the original LinuxCNC GTK PnCConf wizard for:
  - Base Information
  - Screen Configuration
  - Virtual Control Panel (VCP)
  - External Controls
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import json
import os

# External controls — full model lives in dedicated module
from config.ext_controls_config import (  # noqa: F401
    ExternalControlsConfig,
    VFDConfig,
    ButtonJogConfig,
    ButtonJogAxisConfig,
    MPGConfig,
    MPGIncrementRow,
    JoyJogConfig,
    JoyJogAxisMapping,
    OverrideConfig,
)


@dataclass
class AxisConfig:
    name: str = "X"
    travel: float = 200.0
    home_position: float = 0.0
    home_switch_location: float = 0.0
    search_velocity: float = 5.0
    latch_velocity: float = 1.0
    home_sequence: int = 0
    max_velocity: float = 50.0
    max_acceleration: float = 500.0
    ferror: float = 1.0
    min_ferror: float = 0.25
    scale: float = 200.0
    stepgen_maxvel: float = 55.0
    stepgen_maxaccel: float = 550.0
    pid_p: float = 50.0
    pid_i: float = 0.0
    pid_d: float = 0.0
    pid_ff0: float = 0.0
    pid_ff1: float = 1.0
    pid_ff2: float = 0.0
    pid_bias: float = 0.0
    pid_max_output: float = 10.0
    step_time: int = 5000
    step_space: int = 5000
    direction_hold: int = 20000
    direction_setup: int = 20000
    motor_steps_rev: int = 200
    microstep: int = 1
    pulley_ratio: float = 1.0
    leadscrew_pitch: float = 5.0
    worm_ratio: float = 1.0
    encoder_lines: int = 1000


@dataclass
class SpindleConfig:
    analog_max_voltage: float = 10.0
    min_rpm: float = 0.0
    max_rpm: float = 3000.0
    encoder_scale: float = 100.0
    acceleration: float = 200.0
    use_encoder: bool = False
    use_vfd: bool = False
    vfd_type: str = "none"
    spindle_at_speed: bool = True


@dataclass
class MesaPin:
    num: int = 0
    function: str = "Unused"
    pin_type: str = "GPIO"
    invert: bool = False
    extra: str = ""


@dataclass
class MesaConnector:
    name: str = "P2"
    pins: List[MesaPin] = field(default_factory=list)

    def __post_init__(self):
        if not self.pins:
            self.pins = [MesaPin(num=i) for i in range(24)]


@dataclass
class MesaConfig:
    board_name: str = "7i76e"
    firmware: str = "7i76e.bit"
    pwm_base_freq: int = 100000
    pdm_base_freq: int = 6000000
    watchdog_timeout: float = 10.0
    num_encoders: int = 1
    num_stepgens: int = 5
    num_smart_serial: int = 0
    connectors: List[MesaConnector] = field(default_factory=lambda: [
        MesaConnector("P2"), MesaConnector("P3"),
    ])


# ── I/O Port Config (Base Info page) ──────────────────────────────────────────

@dataclass
class IOPortConfig:
    """
    Matches original PnCConf I/O Control section.
    parport_mode: "none" | "one" | "two"
    mesa0/1_type: "PCI" | "Eth" | "Parport"
    """
    parport_mode: str = "none"       # None / One Parport / Two Parports (radio)
    mesa0_enabled: bool = False
    mesa0_type: str = "PCI"
    mesa0_card: str = "7i76e"
    mesa1_enabled: bool = False
    mesa1_type: str = "PCI"
    mesa1_card: str = "5i25"


# ── Machine Options (Base Info page) ──────────────────────────────────────────

@dataclass
class MachineOptionsConfig:
    """Matches Defaults and Options section of original PnCConf Base page."""
    require_home_before_mdi: bool = True
    popup_toolchange_prompt: bool = True
    leave_spindle_on_toolchange: bool = False
    force_individual_homing: bool = False
    move_spindle_up_before_toolchange: bool = False
    restore_joint_position_on_shutdown: bool = False
    random_position_toolchanger: bool = False


# ── Screen Config ─────────────────────────────────────────────────────────────

@dataclass
class ScreenConfig:
    # GUI
    gui_type: str = "axis"
    position_offset: str = "relative"   # relative | machine
    position_feedback: str = "actual"   # actual | commanded
    display_geometry: str = "xyz"

    # Overrides (integer %)
    max_spindle_override: int = 100
    min_spindle_override: int = 50
    max_feed_override: int = 150

    # Velocity (machine units / min)
    default_linear_velocity: float = 25.0
    min_linear_velocity: float = 0.0
    max_linear_velocity: float = 50.0
    default_angular_velocity: float = 25.0
    min_angular_velocity: float = 0.0
    max_angular_velocity: float = 360.0

    # Editor / increments
    editor: str = "gedit"
    increments: str = "1mm .1mm .01mm .001mm"

    # Window
    window_width: int = 800
    window_height: int = 600
    window_x: int = 0
    window_y: int = 0
    force_maximize: bool = False

    # Legacy geometry string (kept for backward compat)
    geometry: str = "800x600+0+0"


# ── VCP Config ────────────────────────────────────────────────────────────────

@dataclass
class VCPConfig:
    # PyVCP
    include_pyvcp: bool = False
    pyvcp_file: str = ""
    pyvcp_use_sample: bool = False
    pyvcp_spindle_speed: bool = False
    pyvcp_spindle_at_speed: bool = False
    pyvcp_zero_x: bool = False
    pyvcp_zero_y: bool = False
    pyvcp_zero_z: bool = False
    pyvcp_zero_a: bool = False

    # GladeVCP
    include_gladevcp: bool = False
    gladevcp_file: str = ""
    gladevcp_use_sample: bool = False
    gladevcp_spindle_speed: bool = False
    gladevcp_spindle_at_speed: bool = False
    gladevcp_zero_x: bool = False
    gladevcp_zero_y: bool = False
    gladevcp_zero_z: bool = False
    gladevcp_zero_a: bool = False

    # Size / position
    panel_width: int = 200
    panel_height: int = 400
    panel_x: int = 0
    panel_y: int = 0
    panel_force_maximize: bool = False

    # Embedding: none | center_tab | right_side | standalone
    embed_panel: str = "none"

    # GTK theme
    follow_system_theme: bool = True


# ── External Controls ─────────────────────────────────────────────────────────

@dataclass
class OptionsConfig:
    num_halui_commands: int = 0
    halui_commands: List[str] = field(default_factory=list)
    use_classicladder: bool = False
    classicladder_program: str = ""
    custom_hal_before: str = ""
    custom_hal_after: str = ""
    custom_programs: List[str] = field(default_factory=list)


@dataclass
class RealtimeConfig:
    use_absolute: bool = False
    use_pid: bool = True
    use_scale: bool = False
    use_mux2: bool = False
    use_lowpass: bool = False
    custom_components: List[str] = field(default_factory=list)


@dataclass
class IOConfig:
    tb6_inputs: List[Dict[str, Any]] = field(default_factory=list)
    tb5_inputs: List[Dict[str, Any]] = field(default_factory=list)
    tb4_analog_outputs: List[Dict[str, Any]] = field(default_factory=list)


# ── Top-level config ──────────────────────────────────────────────────────────

@dataclass
class MachineConfig:
    # Identity
    machine_name: str = "my_machine"
    config_directory: str = os.path.expanduser("~/linuxcnc/configs/my_machine")
    config_type: str = "new"

    # Kinematics
    axis_config: str = "XZ"
    include_spindle: bool = True
    units: str = "metric"

    # Timing
    servo_period_ns: int = 1000000
    recommended_servo_period_ns: int = 1000000   # display-only

    # I/O
    num_io_ports: int = 1
    io_port: IOPortConfig = field(default_factory=IOPortConfig)

    # Machine options
    machine_options: MachineOptionsConfig = field(default_factory=MachineOptionsConfig)

    # Sub-configs
    mesa: MesaConfig = field(default_factory=MesaConfig)
    screen: ScreenConfig = field(default_factory=ScreenConfig)
    vcp: VCPConfig = field(default_factory=VCPConfig)
    external: ExternalControlsConfig = field(default_factory=ExternalControlsConfig)
    options: OptionsConfig = field(default_factory=OptionsConfig)
    realtime: RealtimeConfig = field(default_factory=RealtimeConfig)
    spindle: SpindleConfig = field(default_factory=SpindleConfig)
    io: IOConfig = field(default_factory=IOConfig)

    # Per-axis configs
    axes: Dict[str, AxisConfig] = field(default_factory=lambda: {
        "X": AxisConfig(name="X"),
        "Z": AxisConfig(name="Z"),
    })

    def ensure_axes(self):
        for letter in self.axis_config:
            if letter not in self.axes:
                self.axes[letter] = AxisConfig(name=letter)

    def to_dict(self) -> Dict[str, Any]:
        import dataclasses
        return dataclasses.asdict(self)

    def save(self, path: str):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: str) -> "MachineConfig":
        with open(path) as f:
            data = json.load(f)
        cfg = cls()
        for k, v in data.items():
            if hasattr(cfg, k) and not isinstance(v, (dict, list)):
                setattr(cfg, k, v)
        return cfg

    def to_ini_sections(self) -> Dict[str, Dict[str, str]]:
        """
        Export to LinuxCNC .ini section dict.
        Keys match standard [SECTION] KEY = VALUE format.
        """
        sc = self.screen
        v = self.vcp
        o = self.machine_options

        ini: Dict[str, Dict[str, str]] = {}

        ini["EMC"] = {
            "MACHINE": self.machine_name,
            "DEBUG": "0",
        }

        ini["DISPLAY"] = {
            "DISPLAY": sc.gui_type,
            "POSITION_OFFSET": sc.position_offset.upper(),
            "POSITION_FEEDBACK": sc.position_feedback.upper(),
            "GEOMETRY": sc.display_geometry,
            "MAX_FEED_OVERRIDE": f"{sc.max_feed_override / 100.0:.2f}",
            "MIN_SPINDLE_OVERRIDE": f"{sc.min_spindle_override / 100.0:.2f}",
            "MAX_SPINDLE_OVERRIDE": f"{sc.max_spindle_override / 100.0:.2f}",
            "DEFAULT_LINEAR_VELOCITY": str(sc.default_linear_velocity),
            "MIN_LINEAR_VELOCITY": str(sc.min_linear_velocity),
            "MAX_LINEAR_VELOCITY": str(sc.max_linear_velocity),
            "DEFAULT_ANGULAR_VELOCITY": str(sc.default_angular_velocity),
            "MIN_ANGULAR_VELOCITY": str(sc.min_angular_velocity),
            "MAX_ANGULAR_VELOCITY": str(sc.max_angular_velocity),
            "EDITOR": sc.editor,
            "INCREMENTS": sc.increments,
        }
        if sc.force_maximize:
            ini["DISPLAY"]["WINDOW_SIZE"] = f"{sc.window_width} {sc.window_height}"
            ini["DISPLAY"]["WINDOW_POSITION"] = f"{sc.window_x} {sc.window_y}"

        if v.include_pyvcp and v.pyvcp_file:
            ini["DISPLAY"]["PYVCP"] = v.pyvcp_file

        ini["TRAJ"] = {
            "AXES": str(len(self.axis_config)),
            "COORDINATES": " ".join(self.axis_config),
            "LINEAR_UNITS": "mm" if self.units == "metric" else "inch",
            "ANGULAR_UNITS": "degree",
        }

        ini["EMCMOT"] = {
            "EMCMOT": "motmod",
            "COMM_TIMEOUT": "1.0",
            "SERVO_PERIOD": str(self.servo_period_ns),
        }

        ini["KINS"] = {
            "KINEMATICS": f"trivkins coordinates={self.axis_config}",
            "JOINTS": str(len(self.axis_config)),
        }

        ini["RS274NGC"] = {
            "PARAMETER_FILE": "linuxcnc.var",
        }

        ini["HAL"] = {
            "HALFILE": f"{self.machine_name}.hal",
        }

        return ini

