"""
PNCconf Data Model — Full Feature Parity
=========================================
Dataclass-based configuration matching ALL parameters in the original
LinuxCNC GTK PnCConf wizard, including complete Mesa FPGA support.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
import json
import os

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


# ─────────────────────────────────────────────────────────────────────────────
# Mesa FPGA Hardware Database
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class FirmwareSpec:
    """Describes one firmware blob's capability limits."""
    filename: str
    max_encoders: int
    max_stepgens: int
    max_pwmgens: int
    max_sserials: int
    connectors: Dict[str, int] = field(default_factory=dict)
    description: str = ""


MESA_FIRMWARE_DB: Dict[str, List[FirmwareSpec]] = {
    "5i25": [
        FirmwareSpec("5i25_prob_rf.bit",   3, 5, 1, 0, {"P1": 17, "P2": 17}, "Prob+Step DB25"),
        FirmwareSpec("5i25_sserial.bit",   0, 5, 0, 4, {"P1": 17, "P2": 17}, "Smart Serial DB25"),
        FirmwareSpec("5i25_t7i76d.bit",    1, 5, 1, 2, {"P1": 17, "P2": 17}, "7i76 daughter twin"),
    ],
    "6i25": [
        FirmwareSpec("6i25_prob_rf.bit",   3, 5, 1, 0, {"P1": 17, "P2": 17}, "PCIe Prob+Step"),
    ],
    "7i76e": [
        FirmwareSpec("7i76e.bit",           1, 5, 1, 1, {"P1": 34, "P2": 34}, "Standard 7i76e"),
        FirmwareSpec("7i76e_7i76.bit",      1, 5, 1, 1, {"P1": 34, "P2": 34}, "7i76e + 7i76 daughter"),
        FirmwareSpec("7i76e2x.bit",         2, 10, 2, 2, {"P1": 34, "P2": 34}, "Dual stepgen 7i76e"),
    ],
    "7i92": [
        FirmwareSpec("7i92_5abcg20.bit",   3, 5, 1, 0, {"P1": 17, "P2": 17}, "Ethernet 5-axis"),
        FirmwareSpec("7i92_7i76x2.bit",    2, 10, 2, 2, {"P1": 34, "P2": 34}, "Dual 7i76 daughter"),
    ],
    "7i96": [
        FirmwareSpec("7i96.bit",           1, 5, 1, 1, {"P1": 11, "P2": 5}, "Standard 7i96"),
        FirmwareSpec("7i96_s.bit",         1, 6, 1, 1, {"P1": 11, "P2": 5}, "7i96 with extra step"),
    ],
    "7i96S": [
        FirmwareSpec("7i96s.bit",          1, 6, 1, 1, {"P1": 11, "P2": 5}, "7i96S Rev2"),
    ],
}


def get_firmware_spec(board: str, firmware_file: str) -> Optional[FirmwareSpec]:
    for s in MESA_FIRMWARE_DB.get(board, []):
        if s.filename == firmware_file:
            return s
    return None


def get_firmware_list(board: str) -> List[str]:
    return [s.filename for s in MESA_FIRMWARE_DB.get(board, [])]


def get_all_boards() -> List[str]:
    return list(MESA_FIRMWARE_DB.keys())


# ─────────────────────────────────────────────────────────────────────────────
# Pin function catalog — every valid LinuxCNC signal for Mesa pins
# ─────────────────────────────────────────────────────────────────────────────

# (display_label, hal_pin_template, pin_type)
# Templates: {board}=board name, {pin}=physical pin num (zero-padded to 3),
#            {n}=resource channel index (zero-padded to 2)
PIN_FUNCTION_CATALOG: List[Tuple[str, str, str]] = [
    ("Unused",            "",                                              "GPIO"),
    ("GPIO Input",        "hm2_{board}.0.gpio.{pin:03d}.in",             "GPIO"),
    ("GPIO Output",       "hm2_{board}.0.gpio.{pin:03d}.out",            "GPIO"),

    # StepGen 0-9
    *[item for i in range(10) for item in [
        (f"StepGen-{i} Step",  f"hm2_{{board}}.0.stepgen.{i:02d}.step",  "StepGen"),
        (f"StepGen-{i} Dir",   f"hm2_{{board}}.0.stepgen.{i:02d}.dir",   "StepGen"),
    ]],

    # Encoder 0-3
    *[item for i in range(4) for item in [
        (f"Encoder-{i} A",   f"hm2_{{board}}.0.encoder.{i:02d}.phase-A",      "Encoder"),
        (f"Encoder-{i} B",   f"hm2_{{board}}.0.encoder.{i:02d}.phase-B",      "Encoder"),
        (f"Encoder-{i} Z",   f"hm2_{{board}}.0.encoder.{i:02d}.index-enable", "Encoder"),
    ]],

    # PWM 0-1
    ("PWM-0 Out",         "hm2_{board}.0.pwmgen.00.value",               "PWM"),
    ("PWM-0 Enable",      "hm2_{board}.0.pwmgen.00.enable",              "PWM"),
    ("PWM-1 Out",         "hm2_{board}.0.pwmgen.01.value",               "PWM"),
    ("PWM-1 Enable",      "hm2_{board}.0.pwmgen.01.enable",              "PWM"),

    # Smart Serial 0-3
    *[item for i in range(4) for item in [
        (f"SSerial-{i} TX", f"hm2_{{board}}.0.sserial.0.{i}.tx",         "SSerial"),
        (f"SSerial-{i} RX", f"hm2_{{board}}.0.sserial.0.{i}.rx",         "SSerial"),
    ]],

    # 7i76 on-board signals
    ("Spindle Out",       "hm2_{board}.0.7i76.0.0.spinout",             "GPIO"),
    ("Spindle Enable",    "hm2_{board}.0.7i76.0.0.spinena",             "GPIO"),
    ("Spindle Dir",       "hm2_{board}.0.7i76.0.0.spindir",             "GPIO"),

    # Home and limit switches (generic GPIO inputs)
    ("E-Stop In",         "hm2_{board}.0.gpio.{pin:03d}.in",            "GPIO"),
    ("Amp Enable",        "hm2_{board}.0.gpio.{pin:03d}.out",           "GPIO"),
    ("Amp Fault In",      "hm2_{board}.0.gpio.{pin:03d}.in",            "GPIO"),
    ("Home X",            "hm2_{board}.0.gpio.{pin:03d}.in",            "GPIO"),
    ("Home Y",            "hm2_{board}.0.gpio.{pin:03d}.in",            "GPIO"),
    ("Home Z",            "hm2_{board}.0.gpio.{pin:03d}.in",            "GPIO"),
    ("Home A",            "hm2_{board}.0.gpio.{pin:03d}.in",            "GPIO"),
    ("Limit+ X",          "hm2_{board}.0.gpio.{pin:03d}.in",            "GPIO"),
    ("Limit- X",          "hm2_{board}.0.gpio.{pin:03d}.in",            "GPIO"),
    ("Limit+ Y",          "hm2_{board}.0.gpio.{pin:03d}.in",            "GPIO"),
    ("Limit- Y",          "hm2_{board}.0.gpio.{pin:03d}.in",            "GPIO"),
    ("Limit+ Z",          "hm2_{board}.0.gpio.{pin:03d}.in",            "GPIO"),
    ("Limit- Z",          "hm2_{board}.0.gpio.{pin:03d}.in",            "GPIO"),
    ("Probe In",          "hm2_{board}.0.gpio.{pin:03d}.in",            "GPIO"),
    ("Charge Pump",       "hm2_{board}.0.gpio.{pin:03d}.out",           "GPIO"),
    ("MPG A",             "hm2_{board}.0.encoder.{n:02d}.phase-A",      "Encoder"),
    ("MPG B",             "hm2_{board}.0.encoder.{n:02d}.phase-B",      "Encoder"),
    ("UART TX",           "hm2_{board}.0.uart.0.txdata",                "GPIO"),
    ("UART RX",           "hm2_{board}.0.uart.0.rxdata",                "GPIO"),
]

FUNC_LOOKUP: Dict[str, Tuple[str, str]] = {
    lbl: (tmpl, pt) for lbl, tmpl, pt in PIN_FUNCTION_CATALOG
}
FUNC_TO_TYPE: Dict[str, str] = {lbl: pt for lbl, _, pt in PIN_FUNCTION_CATALOG}
ALL_FUNCTION_LABELS: List[str] = [lbl for lbl, _, _ in PIN_FUNCTION_CATALOG]

STEPGEN_FUNCTIONS = frozenset(lbl for lbl, _, t in PIN_FUNCTION_CATALOG if t == "StepGen")
ENCODER_FUNCTIONS = frozenset(lbl for lbl, _, t in PIN_FUNCTION_CATALOG if t == "Encoder")
PWMGEN_FUNCTIONS  = frozenset(lbl for lbl, _, t in PIN_FUNCTION_CATALOG if t == "PWM")
SSERIAL_FUNCTIONS = frozenset(lbl for lbl, _, t in PIN_FUNCTION_CATALOG if t == "SSerial")

# HAL net signal name for each display label
HAL_NET_NAME: Dict[str, str] = {
    "Unused":         "",
    "GPIO Input":     "gpio-{pin:03d}-in",
    "GPIO Output":    "gpio-{pin:03d}-out",
    "E-Stop In":      "estop-in",
    "Amp Enable":     "amp-enable",
    "Amp Fault In":   "amp-fault",
    "Home X":         "home-x",
    "Home Y":         "home-y",
    "Home Z":         "home-z",
    "Home A":         "home-a",
    "Limit+ X":       "limit-pos-x",
    "Limit- X":       "limit-neg-x",
    "Limit+ Y":       "limit-pos-y",
    "Limit- Y":       "limit-neg-y",
    "Limit+ Z":       "limit-pos-z",
    "Limit- Z":       "limit-neg-z",
    "Probe In":       "probe-in",
    "Charge Pump":    "charge-pump",
    "Spindle Out":    "spindle-vel-cmd",
    "Spindle Enable": "spindle-enable",
    "Spindle Dir":    "spindle-dir",
    "MPG A":          "mpg-a",
    "MPG B":          "mpg-b",
}
# StepGen/Encoder/PWM signals get auto-named in the HAL generator


# ─────────────────────────────────────────────────────────────────────────────
# Mesa dataclasses
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class MesaPin:
    num: int = 0
    function: str = "Unused"
    pin_type: str = "GPIO"
    invert: bool = False
    hal_pin: str = ""   # resolved HAL pin path (generated)

    def resolve_hal(self, board: str) -> str:
        tmpl, _ = FUNC_LOOKUP.get(self.function, ("", ""))
        if tmpl:
            try:
                self.hal_pin = tmpl.format(board=board, pin=self.num, n=0)
            except (KeyError, IndexError):
                self.hal_pin = tmpl
        else:
            self.hal_pin = ""
        return self.hal_pin


@dataclass
class MesaConnector:
    name: str = "P1"
    pins: List[MesaPin] = field(default_factory=list)
    pin_count: int = 24

    def __post_init__(self):
        if not self.pins:
            self.pins = [MesaPin(num=i) for i in range(self.pin_count)]

    def resize(self, count: int):
        current = len(self.pins)
        if count > current:
            for i in range(current, count):
                self.pins.append(MesaPin(num=i))
        elif count < current:
            self.pins = self.pins[:count]
        self.pin_count = count


@dataclass
class SmartSerialChannel:
    channel_num: int = 0
    device: str = "7i76"
    device_address: int = 0


@dataclass
class MesaConfig:
    board_name: str = "7i76e"
    firmware: str = "7i76e.bit"

    # Card network address (Ethernet boards)
    ip_address: str = "192.168.1.121"

    # Signal Frequencies
    pwm_base_freq: int = 100000
    pdm_base_freq: int = 6000000
    watchdog_timeout: float = 10.0       # ms

    # Channel Counts
    num_encoders: int = 1
    num_stepgens: int = 5
    num_pwmgens: int = 0
    num_smart_serial: int = 0
    num_smart_serial_channels: int = 2

    # Smart Serial channels
    sserial_channels: List[SmartSerialChannel] = field(default_factory=list)

    # Daughter-board sanity checks (original PnCConf "Sanity Checks" section)
    check_7i29: bool = False
    check_7i30: bool = False
    check_7i33: bool = False
    check_7i40: bool = False
    check_7i48: bool = False

    # Connector pin tables
    connectors: List[MesaConnector] = field(default_factory=list)

    def __post_init__(self):
        if not self.connectors:
            self._init_connectors_from_firmware()
        if not self.sserial_channels:
            self.sserial_channels = [
                SmartSerialChannel(i) for i in range(self.num_smart_serial_channels)
            ]

    def _init_connectors_from_firmware(self):
        spec = get_firmware_spec(self.board_name, self.firmware)
        if spec:
            self.connectors = [
                MesaConnector(name=conn, pin_count=cnt)
                for conn, cnt in spec.connectors.items()
            ]
        else:
            self.connectors = [MesaConnector("P1"), MesaConnector("P2")]

    def update_from_firmware(self):
        """Clamp channel counts and resize connectors to match selected firmware."""
        spec = get_firmware_spec(self.board_name, self.firmware)
        if spec is None:
            return
        self.num_encoders     = min(self.num_encoders,     spec.max_encoders)
        self.num_stepgens     = min(self.num_stepgens,     spec.max_stepgens)
        self.num_pwmgens      = min(self.num_pwmgens,      spec.max_pwmgens)
        self.num_smart_serial = min(self.num_smart_serial, spec.max_sserials)

        existing = {c.name: c for c in self.connectors}
        self.connectors = []
        for name, cnt in spec.connectors.items():
            if name in existing:
                existing[name].resize(cnt)
                self.connectors.append(existing[name])
            else:
                self.connectors.append(MesaConnector(name=name, pin_count=cnt))

    def firmware_limits(self) -> Optional[FirmwareSpec]:
        return get_firmware_spec(self.board_name, self.firmware)

    def assigned_stepgen_count(self) -> int:
        return sum(
            1 for c in self.connectors
            for p in c.pins if p.function in STEPGEN_FUNCTIONS
        )

    def assigned_encoder_channels(self) -> int:
        nums: set = set()
        for conn in self.connectors:
            for pin in conn.pins:
                if pin.function in ENCODER_FUNCTIONS:
                    try:
                        nums.add(int(pin.function.split("-")[1].split()[0]))
                    except (ValueError, IndexError):
                        pass
        return len(nums)

    def validate_pin_assignments(self) -> List[str]:
        errors: List[str] = []
        spec = self.firmware_limits()

        # Duplicate assignments
        seen: Dict[str, str] = {}
        for conn in self.connectors:
            for pin in conn.pins:
                if pin.function == "Unused":
                    continue
                loc = f"{conn.name}:{pin.num}"
                if pin.function in seen:
                    errors.append(
                        f"Duplicate '{pin.function}' at {loc} and {seen[pin.function]}."
                    )
                else:
                    seen[pin.function] = loc

        # StepGen count
        sg_nums: set = set()
        for conn in self.connectors:
            for pin in conn.pins:
                if pin.function in STEPGEN_FUNCTIONS:
                    try:
                        sg_nums.add(int(pin.function.split("-")[1].split()[0]))
                    except (ValueError, IndexError):
                        pass
        if spec and len(sg_nums) > spec.max_stepgens:
            errors.append(
                f"StepGen channels used ({len(sg_nums)}) exceeds "
                f"firmware max ({spec.max_stepgens})."
            )

        # Encoder count
        enc_nums: set = set()
        for conn in self.connectors:
            for pin in conn.pins:
                if pin.function in ENCODER_FUNCTIONS:
                    try:
                        enc_nums.add(int(pin.function.split("-")[1].split()[0]))
                    except (ValueError, IndexError):
                        pass
        if spec and len(enc_nums) > spec.max_encoders:
            errors.append(
                f"Encoder channels used ({len(enc_nums)}) exceeds "
                f"firmware max ({spec.max_encoders})."
            )

        return errors


# ─────────────────────────────────────────────────────────────────────────────
# All other config dataclasses
# ─────────────────────────────────────────────────────────────────────────────

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
    pid_deadband: float = 0.0
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
class IOPortConfig:
    parport_mode: str = "none"
    mesa0_enabled: bool = False
    mesa0_type: str = "Eth"
    mesa0_card: str = "7i76e"
    mesa1_enabled: bool = False
    mesa1_type: str = "PCI"
    mesa1_card: str = "5i25"


@dataclass
class MachineOptionsConfig:
    require_home_before_mdi: bool = True
    popup_toolchange_prompt: bool = True
    leave_spindle_on_toolchange: bool = False
    force_individual_homing: bool = False
    move_spindle_up_before_toolchange: bool = False
    restore_joint_position_on_shutdown: bool = False
    random_position_toolchanger: bool = False


@dataclass
class ScreenConfig:
    gui_type: str = "qtvcp my_panel"   # meukron default
    position_offset: str = "relative"
    position_feedback: str = "actual"
    display_geometry: str = "xyz"
    max_spindle_override: int = 100
    min_spindle_override: int = 50
    max_feed_override: int = 150
    default_linear_velocity: float = 25.0
    min_linear_velocity: float = 0.0
    max_linear_velocity: float = 50.0
    default_angular_velocity: float = 25.0
    min_angular_velocity: float = 0.0
    max_angular_velocity: float = 360.0
    editor: str = "gedit"
    increments: str = "1mm .1mm .01mm .001mm"
    window_width: int = 800
    window_height: int = 600
    window_x: int = 0
    window_y: int = 0
    force_maximize: bool = False
    geometry: str = "800x600+0+0"


# ─────────────────────────────────────────────────────────────────────────────
# Control Panel (custom GUI panel selection — in-memory only during session)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ControlPanelConfig:
    """Holds user-selected custom GUI panel data.

    Not persisted anywhere except through the generated INI file
    (PANEL_NAME / PANEL_PATH keys inside [DISPLAY]).  No JSON or
    external files are involved.
    """
    panel_name: str = ""   # human label, e.g. "my_panel"
    panel_path: str = ""   # absolute path to panel file or directory

    @property
    def is_configured(self) -> bool:
        """True only when both fields carry non-blank values."""
        return bool(self.panel_name.strip() and self.panel_path.strip())


@dataclass
class VCPConfig:
    include_pyvcp: bool = False
    pyvcp_file: str = ""
    pyvcp_use_sample: bool = False
    pyvcp_spindle_speed: bool = False
    pyvcp_spindle_at_speed: bool = False
    pyvcp_zero_x: bool = False
    pyvcp_zero_y: bool = False
    pyvcp_zero_z: bool = False
    pyvcp_zero_a: bool = False
    include_gladevcp: bool = False
    gladevcp_file: str = ""
    gladevcp_use_sample: bool = False
    gladevcp_spindle_speed: bool = False
    gladevcp_spindle_at_speed: bool = False
    gladevcp_zero_x: bool = False
    gladevcp_zero_y: bool = False
    gladevcp_zero_z: bool = False
    gladevcp_zero_a: bool = False
    panel_width: int = 200
    panel_height: int = 400
    panel_x: int = 0
    panel_y: int = 0
    panel_force_maximize: bool = False
    embed_panel: str = "none"
    follow_system_theme: bool = True


@dataclass
class OptionsConfig:
    # HALUI MDI commands (up to 15, mapped to halui.mdi-command-00 .. -14)
    num_halui_commands: int = 0
    halui_commands: List[str] = field(default_factory=list)

    # ClassicLadder PLC
    use_classicladder: bool = False
    # "none" | "blank" | "estop" | "serialmodbus" | "custom"
    classicladder_type: str = "none"
    classicladder_program: str = ""
    classicladder_use_hal_connections: bool = False

    # Custom HAL snippets
    custom_hal_before: str = ""
    custom_hal_after: str = ""
    custom_programs: List[str] = field(default_factory=list)


@dataclass
class ComponentInstance:
    """One row in the custom component loader table."""
    load_cmd: str = ""           # e.g. "loadrt  my_comp"
    thread_cmd: str = ""         # e.g. "addf my_comp.0  servo-thread"
    thread: str = "servo-thread" # "servo-thread" | "base-thread"


@dataclass
class RealtimeConfig:
    # Standard components — instance counts (0 = don't load)
    count_absolute: int = 0
    count_pid: int = 0
    count_scale: int = 0
    count_mux2: int = 0
    count_mux4: int = 0
    count_mux8: int = 0
    count_mux16: int = 0
    count_lowpass: int = 0
    count_limit1: int = 0
    count_limit2: int = 0
    count_limit3: int = 0
    count_not: int = 0
    count_and2: int = 0
    count_or2: int = 0
    count_xor2: int = 0
    count_estop_latch: int = 0
    count_logic: int = 0
    count_oneshot: int = 0
    count_toggle: int = 0
    count_near: int = 0
    count_sum2: int = 0
    count_wcomp: int = 0
    count_conv_float_s32: int = 0
    count_conv_s32_float: int = 0
    count_conv_bit_s32: int = 0
    count_conv_s32_bit: int = 0

    # Thread assignment per component (for components with thread affinity)
    # "servo-thread" | "base-thread"
    thread_absolute: str = "servo-thread"
    thread_pid: str = "servo-thread"
    thread_scale: str = "servo-thread"
    thread_mux2: str = "servo-thread"
    thread_mux4: str = "servo-thread"
    thread_mux8: str = "servo-thread"
    thread_mux16: str = "servo-thread"
    thread_lowpass: str = "servo-thread"
    thread_limit1: str = "servo-thread"
    thread_limit2: str = "servo-thread"
    thread_limit3: str = "servo-thread"
    thread_not: str = "base-thread"
    thread_and2: str = "base-thread"
    thread_or2: str = "base-thread"
    thread_xor2: str = "base-thread"
    thread_estop_latch: str = "servo-thread"
    thread_logic: str = "servo-thread"
    thread_oneshot: str = "base-thread"
    thread_toggle: str = "base-thread"
    thread_near: str = "servo-thread"
    thread_sum2: str = "servo-thread"
    thread_wcomp: str = "servo-thread"
    thread_conv_float_s32: str = "servo-thread"
    thread_conv_s32_float: str = "servo-thread"
    thread_conv_bit_s32: str = "servo-thread"
    thread_conv_s32_bit: str = "servo-thread"

    # Custom component command rows
    custom_components: List[Any] = field(default_factory=list)

    # Backward-compat booleans (derived from counts > 0)
    @property
    def use_absolute(self) -> bool: return self.count_absolute > 0
    @property
    def use_pid(self) -> bool: return self.count_pid > 0
    @property
    def use_scale(self) -> bool: return self.count_scale > 0
    @property
    def use_mux2(self) -> bool: return self.count_mux2 > 0
    @property
    def use_lowpass(self) -> bool: return self.count_lowpass > 0


@dataclass
class IOConfig:
    tb6_inputs: List[Dict[str, Any]] = field(default_factory=list)
    tb5_inputs: List[Dict[str, Any]] = field(default_factory=list)
    tb4_analog_outputs: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class MachineConfig:
    machine_name: str = "meukron"
    config_directory: str = os.path.expanduser("~/linuxcnc/configs/meukron")
    config_type: str = "new"
    axis_config: str = "XYZ"
    include_spindle: bool = True
    units: str = "metric"
    servo_period_ns: int = 1000000
    recommended_servo_period_ns: int = 1000000
    num_io_ports: int = 1
    io_port: IOPortConfig = field(default_factory=IOPortConfig)
    machine_options: MachineOptionsConfig = field(default_factory=MachineOptionsConfig)
    mesa: MesaConfig = field(default_factory=MesaConfig)
    screen: ScreenConfig = field(default_factory=ScreenConfig)
    vcp: VCPConfig = field(default_factory=VCPConfig)
    external: ExternalControlsConfig = field(default_factory=ExternalControlsConfig)
    options: OptionsConfig = field(default_factory=OptionsConfig)
    realtime: RealtimeConfig = field(default_factory=RealtimeConfig)
    spindle: SpindleConfig = field(default_factory=SpindleConfig)
    io: IOConfig = field(default_factory=IOConfig)
    control_panel: ControlPanelConfig = field(default_factory=ControlPanelConfig)
    axes: Dict[str, AxisConfig] = field(default_factory=lambda: {
        "X": AxisConfig(name="X"),
        "Y": AxisConfig(name="Y"),
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
        sc = self.screen
        v = self.vcp
        m = self.mesa
        ini: Dict[str, Dict[str, str]] = {}

        ini["EMC"] = {"MACHINE": self.machine_name, "DEBUG": "0"}
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
            "EDITOR": sc.editor,
            "INCREMENTS": sc.increments,
        }
        if v.include_pyvcp and v.pyvcp_file:
            ini["DISPLAY"]["PYVCP"] = v.pyvcp_file
        # Control panel — only written when the user has explicitly configured one
        if self.control_panel.is_configured:
            ini["DISPLAY"]["PANEL_NAME"] = self.control_panel.panel_name
            ini["DISPLAY"]["PANEL_PATH"] = self.control_panel.panel_path

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
        ini["RS274NGC"] = {"PARAMETER_FILE": "linuxcnc.var"}
        ini["HAL"] = {"HALFILE": f"{self.machine_name}.hal"}
        ini["HOSTMOT2"] = {
            "DRIVER": "hm2_eth",
            "BOARD": m.board_name,
            "CONFIG": (
                f"firmware={m.firmware} "
                f"num_encoders={m.num_encoders} "
                f"num_stepgens={m.num_stepgens} "
                f"num_pwmgens={m.num_pwmgens}"
            ),
        }
        return ini
