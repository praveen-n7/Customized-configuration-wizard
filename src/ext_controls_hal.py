"""
External Controls HAL Generator
================================
Generates HAL snippets for all external control devices.
Called by the main HALGenerator when external controls are enabled.

Each method returns a list of HAL text lines.
The caller inserts these into the appropriate position in the main .hal file.
"""

from __future__ import annotations
from typing import List
from config.ext_controls_config import (
    ExternalControlsConfig, VFDConfig, ButtonJogConfig,
    MPGConfig, JoyJogConfig, OverrideConfig,
)


class ExternalControlsHAL:
    def __init__(self, ext: ExternalControlsConfig, machine_name: str,
                 axis_config: str = "XYZ"):
        self.ext  = ext
        self.name = machine_name
        self.axes = list(axis_config)

    # ── Public entry point ────────────────────────────────────────────────────

    def generate_all(self) -> str:
        """Return complete HAL text for all enabled external controls."""
        blocks: List[List[str]] = []

        if self.ext.use_serial_vfd:
            blocks.append(self._vfd_hal())
        if self.ext.use_ext_button_jogging:
            blocks.append(self._button_jog_hal())
        if self.ext.use_mpg:
            blocks.append(self._mpg_hal())
        if self.ext.use_usb_jogging:
            blocks.append(self._joy_jog_hal())
        if self.ext.use_feed_override:
            blocks.append(self._override_hal(
                self.ext.feed_override, "fo", "Feed Override",
                "halui.feed-override.scale"))
        if self.ext.use_max_vel_override:
            blocks.append(self._override_hal(
                self.ext.max_vel_override, "mvo", "Max Velocity Override",
                "halui.max-velocity.value"))
        if self.ext.use_spindle_override:
            blocks.append(self._override_hal(
                self.ext.spindle_override, "so", "Spindle Override",
                "halui.spindle.0.override.scale"))

        return "\n".join(line for block in blocks for line in block)

    # ── VFD ───────────────────────────────────────────────────────────────────

    def _vfd_hal(self) -> List[str]:
        v = self.ext.vfd
        lines = [
            "",
            "# ── Serial VFD ─────────────────────────────────────────────────",
            v.hal_loadusr(self.name),
            "",
            f"# Spindle → VFD connections",
            f"net spindle-speed-cmd  {v.hal_spindle_speed_in}  => vfd.speed-command",
            f"net spindle-on         {v.hal_spindle_enable}    => vfd.enable",
            f"net spindle-fwd        {v.hal_spindle_fwd}       => vfd.spindle-fwd",
            f"net spindle-rev        {v.hal_spindle_rev}       => vfd.spindle-rev",
            "",
            f"# VFD → motion at-speed feedback",
            f"net spindle-at-speed   vfd.at-speed              => spindle.0.at-speed",
        ]
        if v.accel_time:
            lines += [
                f"setp vfd.accel-time {v.accel_time:.1f}",
                f"setp vfd.decel-time {v.decel_time:.1f}",
            ]
        if v.spindle_at_speed_tolerance:
            lines.append(
                f"setp vfd.at-speed-tolerance {v.spindle_at_speed_tolerance:.3f}"
            )
        return lines

    # ── Button Jog ────────────────────────────────────────────────────────────

    def _button_jog_hal(self) -> List[str]:
        bj = self.ext.button_jog
        lines = [
            "",
            "# ── External Button Jogging ─────────────────────────────────────",
            "loadrt or2  count=2",   # for fast/slow mux if needed
        ]
        for ax_letter, ax_cfg in bj.axes.items():
            if not ax_cfg.enabled:
                continue
            idx = self.axes.index(ax_letter) if ax_letter in self.axes else 0
            pos_pin = ax_cfg.pin_positive or f"# ASSIGN_PIN_jog_{ax_letter}_pos"
            neg_pin = ax_cfg.pin_negative or f"# ASSIGN_PIN_jog_{ax_letter}_neg"
            if ax_cfg.invert_positive:
                lines.append(f"net jog-{ax_letter}-plus-raw  {pos_pin}")
                lines.append(f"# (invert positive button)")
            else:
                lines.append(
                    f"net jog-{ax_letter}-plus  {pos_pin}"
                    f"  => halui.jog.{idx}.plus"
                )
            if ax_cfg.invert_negative:
                lines.append(f"net jog-{ax_letter}-minus-raw  {neg_pin}")
                lines.append(f"# (invert negative button)")
            else:
                lines.append(
                    f"net jog-{ax_letter}-minus {neg_pin}"
                    f"  => halui.jog.{idx}.minus"
                )
            if ax_cfg.jog_speed > 0:
                lines.append(
                    f"setp halui.jog-speed {ax_cfg.jog_speed:.3f}"
                )
        if bj.use_fast_button and bj.fast_button_pin:
            lines += [
                f"net jog-fast  {bj.fast_button_pin}  => halui.jog-speed",
                f"setp halui.jog-speed {bj.slow_speed:.3f}",
            ]
        return lines

    # ── MPG ───────────────────────────────────────────────────────────────────

    def _mpg_hal(self) -> List[str]:
        m = self.ext.mpg
        lines = [
            "",
            "# ── MPG (Manual Pulse Generator) ───────────────────────────────",
        ]

        if m.mode == "use_mpg":
            # Realtime encoder component
            lines += [
                "loadrt encoder num_chan=1",
                "addf encoder.update-counters  base-thread",
                "addf encoder.capture-position servo-thread",
                "",
                f"setp encoder.0.position-scale {m.scale:.4f}",
            ]
            a_pin = m.encoder_a_pin or "# ASSIGN_MPG_A_PIN"
            b_pin = m.encoder_b_pin or "# ASSIGN_MPG_B_PIN"
            lines += [
                f"net mpg-a  {a_pin}  => encoder.0.phase-A",
                f"net mpg-b  {b_pin}  => encoder.0.phase-B",
            ]
            if m.encoder_index_pin:
                lines.append(
                    f"net mpg-idx {m.encoder_index_pin}  => encoder.0.phase-Z"
                )
            if m.mpg_axis:
                ax_idx = self.axes.index(m.mpg_axis) if m.mpg_axis in self.axes else 0
                lines += [
                    f"net mpg-pos  encoder.0.position  => halui.jog.{ax_idx}.analog",
                    f"setp halui.jog.{ax_idx}.jog-accel-fraction 0.5",
                ]
            else:
                # Axis-select switches
                lines.append("# MPG axis-select switches:")
                for ax, pin in m.axis_select_pins.items():
                    if not pin:
                        continue
                    ax_idx = self.axes.index(ax) if ax in self.axes else 0
                    lines.append(
                        f"net mpg-sel-{ax}  {pin}  => halui.jog.{ax_idx}.jog-enable"
                    )

        elif m.mode in ("use_switches", "use_increments"):
            # Digital-input increment selection
            lines += [
                "loadrt mux_generic config=\"bb4\"",
                "addf mux_generic.0  servo-thread",
                "",
            ]
            for pin_label, pin_name in [
                ("a", m.switch_pin_a), ("b", m.switch_pin_b),
                ("c", m.switch_pin_c), ("d", m.switch_pin_d),
            ]:
                if pin_name:
                    lines.append(
                        f"net mpg-sw-{pin_label}  {pin_name}  => mux_generic.0.sel{pin_label.upper()}"
                    )
            # Load increment table into mux inputs
            for i, row in enumerate(m.increment_table):
                lines.append(
                    f"setp mux_generic.0.in{i:02d} {row.increment:.6f}"
                )
            lines += [
                "net mpg-increment  mux_generic.0.out  => halui.jog-speed",
            ]

        # Debounce
        if m.debounce_time > 0:
            lines += [
                f"loadrt debounce cfg=4",
                f"addf debounce.0  servo-thread",
                f"setp debounce.0.delay {m.debounce_time:.3f}",
            ]

        # Gray code
        if m.use_gray_code:
            lines.append("# Gray-code decoding: set encoder.0.counter-mode to quadrature")
            lines.append("setp encoder.0.counter-mode 0")

        return lines

    # ── USB Joystick ──────────────────────────────────────────────────────────

    def _joy_jog_hal(self) -> List[str]:
        j = self.ext.joy_jog
        lines = [
            "",
            "# ── USB Joystick Jogging ────────────────────────────────────────",
            f"loadusr -W hal_input -KRAL {j.device}",
            "",
        ]
        for mapping in j.axis_mappings:
            ax_idx = self.axes.index(mapping.machine_axis) \
                     if mapping.machine_axis in self.axes else 0
            src = f"{j.hal_name}.abs-{mapping.joystick_axis}-position"
            if mapping.invert:
                lines += [
                    f"loadrt negate count=1",
                    f"net joy-raw-{mapping.machine_axis}  {src}  => negate.0.in",
                    f"net joy-{mapping.machine_axis}  negate.0.out  "
                    f"=> halui.jog.{ax_idx}.analog",
                ]
            else:
                lines.append(
                    f"net joy-{mapping.machine_axis}  {src}  "
                    f"=> halui.jog.{ax_idx}.analog"
                )
            if mapping.scale != 1.0:
                lines.append(
                    f"setp halui.jog.{ax_idx}.analog-scale {mapping.scale:.4f}"
                )
        if j.deadzone > 0:
            lines += [
                f"loadrt deadzone count={len(j.axis_mappings)}",
                f"setp deadzone.0.zone {j.deadzone:.3f}",
            ]
        # Button mappings
        for btn_idx, func in j.button_map.items():
            lines.append(
                f"net joy-btn-{btn_idx}  {j.hal_name}.btn-{btn_idx}  => {func}"
            )
        return lines

    # ── Generic Override (FO / MVO / SO) ─────────────────────────────────────

    def _override_hal(self, ov: OverrideConfig, prefix: str,
                      label: str, target: str) -> List[str]:
        lines = [
            "",
            f"# ── {label} ──────────────────────────────────────────────────",
        ]

        if ov.mode == "encoder":
            lines += [
                "loadrt encoder num_chan=1",
                "addf encoder.update-counters  base-thread",
                "addf encoder.capture-position servo-thread",
                f"setp encoder.0.position-scale {ov.counts_per_revolution}",
            ]
            if ov.encoder_a_pin:
                lines.append(
                    f"net {prefix}-enc-a  {ov.encoder_a_pin}  => encoder.0.phase-A"
                )
            if ov.encoder_b_pin:
                lines.append(
                    f"net {prefix}-enc-b  {ov.encoder_b_pin}  => encoder.0.phase-B"
                )
            lines.append(
                f"net {prefix}-value  encoder.0.position  => {target}"
            )

        elif ov.mode == "analog":
            if ov.filter_time > 0:
                lines += [
                    "loadrt lowpass count=1",
                    "addf lowpass.0  servo-thread",
                    f"setp lowpass.0.gain {ov.filter_time:.4f}",
                ]
                if ov.analog_pin:
                    lines += [
                        f"net {prefix}-raw  {ov.analog_pin}  => lowpass.0.in",
                        f"net {prefix}-filt lowpass.0.out  => {target}",
                    ]
            else:
                if ov.analog_pin:
                    lines.append(
                        f"net {prefix}-value  {ov.analog_pin}  => {target}"
                    )

        elif ov.mode == "switches":
            n = max(len(ov.switch_ladder), 1)
            lines += [
                f"loadrt sum2 count={n}",
                f"addf sum2.0  servo-thread",
            ]
            for i, entry in enumerate(ov.switch_ladder):
                pin = entry.get("pin", "")
                val = entry.get("value", 0.0)
                if pin:
                    lines += [
                        f"net {prefix}-sw{i}  {pin}  => sum2.0.in{i}",
                        f"setp sum2.0.gain{i} {val:.4f}",
                    ]
            lines.append(f"net {prefix}-value  sum2.0.out  => {target}")

        if ov.scale != 1.0:
            lines += [
                "loadrt scale count=1",
                "addf scale.0  servo-thread",
                f"setp scale.0.gain {ov.scale:.6f}",
            ]

        return lines
