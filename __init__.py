from .base_page import BasePage
from .page_welcome import WelcomePage
from .page_config_type import ConfigTypePage
from .page_base_info import BaseMachineInfoPage
from .page_screen_config import ScreenConfigPage
from .page_vcp_ext_mesa import VCPPage, ExternalControlsPage, MesaConfigPage
from .page_connectors import ConnectorsPage
from .page_motor_scale import IO7i76Page, MotorConfigPage, AxisScalePage
from .page_axis_spindle_opts import (
    AxisConfigPage, SpindleConfigPage, OptionsPage, RealtimePage
)
from .page_finish import FinishPage

__all__ = [
    "BasePage", "WelcomePage", "ConfigTypePage", "BaseMachineInfoPage",
    "ScreenConfigPage", "VCPPage", "ExternalControlsPage", "MesaConfigPage",
    "ConnectorsPage", "IO7i76Page", "MotorConfigPage", "AxisScalePage",
    "AxisConfigPage", "SpindleConfigPage", "OptionsPage", "RealtimePage",
    "FinishPage",
]
