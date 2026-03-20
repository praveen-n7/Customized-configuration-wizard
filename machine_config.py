"""
PNCconf Data Model
==================
Central dataclass-based configuration store for the wizard.
All pages read/write from this model; HAL/INI generators consume it.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import json
import os


# ──────────────────────────────────────────────────────────────────────────────
# Sub-models
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class AxisConfig:
    name: str = "X"
    travel: float = 200.0           # mm
    home_position: float = 0.0
    home_switch_location: float = 0.0
    search_velocity: float = 5.0    # mm/s
    latch_velocity: float = 1.0     # mm/s
    home_sequence: int = 0
    max_velocity: float = 50.0      # mm/s
    max_acceleration: float = 500.0 # mm/s²
    ferror: float = 1.0
    min_ferror: float = 0.25
    scale: float = 200.0            # steps/mm or encoder counts/mm
    stepgen_maxvel: float = 55.0
    stepgen_maxaccel: float = 550.0

    # PID
    pid_p: float = 50.0
    pid_i: float = 0.0
    pid_d: float = 0.0
    pid_ff0: float = 0.0
    pid_ff1: float = 1.0
    pid_ff2: float = 0.0
    pid_bias: float = 0.0
    pid_max_output: float = 10.0

    # Stepper timing (ns)
    step_time: int = 5000
    step_space: int = 5000
    direction_hold: int = 20000
    direction_setup: int = 20000

    # Scale calculation inputs
    motor_steps_rev: int = 200
    microstep: int = 1
    pulley_ratio: float = 1.0
    leadscrew_pitch: float = 5.0    # mm/rev
    worm_ratio: float = 1.0
    encoder_lines: int = 1000


@dataclass
class SpindleConfig:
    analog_max_voltage: float = 10.0
    min_rpm: float = 0.0
    max_rpm: float = 3000.0
    encoder_scale: float = 100.0     # counts/rev
    acceleration: float = 200.0      # RPM/s
    use_encoder: bool = False
    use_vfd: bool = False
    vfd_type: str = "none"           # none, gs2, vfs11, hy_vfd, etc.
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
    pwm_base_freq: int = 100000       # Hz
    pdm_base_freq: int = 6000000      # Hz
    watchdog_timeout: float = 10.0    # ms
    num_encoders: int = 1
    num_stepgens: int = 5
    num_smart_serial: int = 0
    connectors: List[MesaConnector] = field(default_factory=lambda: [
        MesaConnector("P2"),
        MesaConnector("P3"),
    ])


@dataclass
class ScreenConfig:
    gui_type: str = "axis"            # axis, gmoccapy, touchy, qtplasmac
    position_offset: str = "relative"
    geometry: str = "800x600+0+0"
    max_feed_override: float = 1.5
    max_spindle_override: float = 1.5
    editor: str = "gedit"
    increments: str = "1mm .1mm .01mm"


@dataclass
class VCPConfig:
    include_pyvcp: bool = False
    pyvcp_file: str = ""
    include_gladevcp: bool = False
    gladevcp_file: str = ""
    embed_panel: str = "none"         # none, side, bottom


@dataclass
class ExternalControlsConfig:
    use_serial_vfd: bool = False
    use_ext_jogging: bool = False
    use_mpg: bool = False
    mpg_increments: str = "0.1 0.01 0.001"
    use_feed_override: bool = False
    use_max_vel_override: bool = False
    use_spindle_override: bool = False
    use_usb_jogging: bool = False


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
    tb6_inputs: List[Dict[str, Any]] = field(default_factory=list)   # 7i76 TB6
    tb5_inputs: List[Dict[str, Any]] = field(default_factory=list)   # 7i76 TB5
    tb4_analog_outputs: List[Dict[str, Any]] = field(default_factory=list)


# ──────────────────────────────────────────────────────────────────────────────
# Top-level config model
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class MachineConfig:
    # ── Identification ──────────────────────────────────────────────────────
    machine_name: str = "my_machine"
    config_directory: str = os.path.expanduser("~/linuxcnc/configs/my_machine")
    config_type: str = "new"              # "new" | "modify"

    # ── Kinematics ──────────────────────────────────────────────────────────
    axis_config: str = "XZ"               # XZ, XYZ, XYZA, XYZC, etc.
    units: str = "metric"                 # "metric" | "imperial"
    servo_period_ns: int = 1000000        # 1ms default

    # ── I/O ─────────────────────────────────────────────────────────────────
    num_io_ports: int = 1

    # ── Sub-configs ─────────────────────────────────────────────────────────
    mesa: MesaConfig = field(default_factory=MesaConfig)
    screen: ScreenConfig = field(default_factory=ScreenConfig)
    vcp: VCPConfig = field(default_factory=VCPConfig)
    external: ExternalControlsConfig = field(default_factory=ExternalControlsConfig)
    options: OptionsConfig = field(default_factory=OptionsConfig)
    realtime: RealtimeConfig = field(default_factory=RealtimeConfig)
    spindle: SpindleConfig = field(default_factory=SpindleConfig)
    io: IOConfig = field(default_factory=IOConfig)

    # ── Per-axis configs ─────────────────────────────────────────────────────
    axes: Dict[str, AxisConfig] = field(default_factory=lambda: {
        "X": AxisConfig(name="X"),
        "Z": AxisConfig(name="Z"),
    })

    def ensure_axes(self):
        """Create AxisConfig entries for each letter in axis_config."""
        for letter in self.axis_config:
            if letter not in self.axes:
                self.axes[letter] = AxisConfig(name=letter)

    # ── Serialisation ────────────────────────────────────────────────────────
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serialisable dict (simple approach)."""
        import dataclasses
        return dataclasses.asdict(self)

    def save(self, path: str):
        """Save configuration as JSON."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: str) -> "MachineConfig":
        """Load configuration from JSON (basic flat-restore)."""
        with open(path) as f:
            data = json.load(f)
        cfg = cls()
        # Shallow restore top-level primitives
        for k, v in data.items():
            if hasattr(cfg, k) and not isinstance(v, (dict, list)):
                setattr(cfg, k, v)
        return cfg
