# PNCconf Qt Wizard

A production-grade LinuxCNC Mesa card configuration wizard built with **PyQt6** (or PySide6) using a modular, stacked-page architecture.

---

## Features

- **16-page wizard** matching the full logical flow of LinuxCNC PNCconf
- **Dark industrial theme** — consistent `#1E1E2E` / `#2A2A3C` / `#5E81AC` palette
- **Modular page system** — each page is an independent `BasePage` subclass
- **Central data model** — all pages read/write a single `MachineConfig` dataclass
- **HAL & INI generators** — produce ready-to-use LinuxCNC configuration files
- **Sidebar navigation** with group headers and completion indicators
- **Live scale calculator** for stepper/servo drive train math
- **Mesa connector pin assignment** with per-pin function and invert tables
- **7i76 I/O assignment** for TB4/TB5/TB6 terminal blocks

---

## Requirements

```
Python >= 3.10
PyQt6 >= 6.4   (or PySide6 >= 6.4)
```

Install:

```bash
pip install PyQt6
# or
pip install PySide6
```

---

## Project Structure

```
pncconf_wizard/
│
├── main.py                     # Entry point
├── wizard_controller.py        # QMainWindow + navigation engine
│
├── config/
│   ├── __init__.py
│   └── machine_config.py       # MachineConfig dataclass hierarchy
│
├── hal_generator/
│   ├── __init__.py
│   ├── hal_gen.py              # HAL file generator
│   └── ini_gen.py              # INI file generator
│
├── ui_theme/
│   ├── __init__.py
│   └── stylesheet.py           # Global dark industrial QSS stylesheet
│
└── pages/
    ├── __init__.py
    ├── base_page.py            # Abstract BasePage (populate/save/validate)
    ├── page_welcome.py         # Step 1: Welcome
    ├── page_config_type.py     # Step 2: New vs Modify
    ├── page_base_info.py       # Step 3: Machine name, axes, Mesa board
    ├── page_screen_config.py   # Step 4: GUI type, overrides, editor
    ├── page_vcp_ext_mesa.py    # Steps 5-7: VCP, External Controls, Mesa config
    ├── page_connectors.py      # Step 8: P2/P3 pin assignment tables
    ├── page_motor_scale.py     # Steps 9-11: 7i76 I/O, Motor PID, Scale calc
    ├── page_axis_spindle_opts.py  # Steps 12-15: Axis, Spindle, Options, RT
    └── page_finish.py          # Step 16: Summary + file generation
```

---

## Running

```bash
cd pncconf_wizard
python main.py
```

---

## Wizard Page Flow

| # | Page | Key Config |
|---|------|-----------|
| 1 | Welcome | Intro |
| 2 | Configuration Type | New / Modify existing |
| 3 | Base Machine Info | Name, axes, Mesa board, servo period |
| 4 | Screen Configuration | GUI type, geometry, overrides |
| 5 | Virtual Control Panel | PyVCP / GladeVCP embedding |
| 6 | External Controls | MPG, VFD, joystick, override wheels |
| 7 | Mesa Card Config | Firmware, PWM/PDM freq, watchdog |
| 8 | Connector Pin Assignment | P2/P3 per-pin function & invert |
| 9 | 7i76 I/O Config | TB4/TB5/TB6 digital & analog I/O |
| 10 | Motor Configuration | PID, stepper timing, motion limits |
| 11 | Axis Scale Calculation | Drive train → steps/mm |
| 12 | Axis Configuration | Travel, home, homing velocities |
| 13 | Spindle Configuration | RPM range, encoder, analog out |
| 14 | Options | HALUI, ClassicLadder, custom HAL |
| 15 | Realtime Components | HAL kernel module selection |
| 16 | Finish | Summary + generate INI + HAL |

---

## Architecture Patterns

### BasePage contract

Every page subclasses `BasePage` and implements three methods:

```python
class MyPage(BasePage):
    PAGE_TITLE    = "My Page"
    PAGE_SUBTITLE = "Description of what this page configures"

    def populate(self, cfg: MachineConfig):
        """Load config → widgets (called on page entry)"""

    def save(self, cfg: MachineConfig):
        """Write widgets → config (called on page exit)"""

    def validate(self) -> tuple[bool, str]:
        """Return (True, '') or (False, 'Error message')"""
```

### Navigation flow

```
WizardController._go_next()
  ├─ current_page.validate()   → abort if invalid
  ├─ current_page.save(cfg)    → persist widget state
  ├─ step.completed = True     → mark sidebar green
  └─ _go_to(next_index)
       ├─ next_page.populate(cfg)   → load fresh state
       ├─ stack.setCurrentWidget()  → switch visible page
       ├─ header.update()           → update title bar
       └─ navbar.update_state()     → update progress + buttons
```

### Data model

All pages share a single `MachineConfig` instance owned by `WizardController`.
Sub-configs are plain Python dataclasses — no Qt coupling.

```python
cfg = MachineConfig()
cfg.machine_name         # str
cfg.axis_config          # "XZ", "XYZ", etc.
cfg.mesa.board_name      # "7i76e"
cfg.axes["X"].scale      # float (steps/mm)
cfg.spindle.max_rpm      # float
```

### File generation

```python
from hal_generator import HALGenerator, INIGenerator

gen_ini = INIGenerator(cfg)
ini_content = gen_ini.generate()   # → str
gen_ini.write("/path/to/config/")  # writes machine.ini

gen_hal = HALGenerator(cfg)
hal_content = gen_hal.generate_machine_hal()   # → str
gen_hal.write_all("/path/to/config/")          # writes machine.hal + custom.hal
```

---

## Extending the Wizard

**Adding a new page:**

1. Create `pages/page_myfeature.py` inheriting from `BasePage`
2. Implement `populate`, `save`, `validate`
3. Import and add to `pages/__init__.py`
4. Register in `WizardController._init_pages()` with a label and group

**Adding a new config field:**

1. Add field to the appropriate dataclass in `config/machine_config.py`
2. Add `populate`/`save` calls in the relevant page
3. Reference in `hal_generator/` or `ini_gen.py` as needed

---

## License

MIT — free for use with LinuxCNC and related open-source CNC projects.
