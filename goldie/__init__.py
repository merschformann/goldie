from .__about__ import __version__
from .comparison import (
    ConfigCompareJson,
    ConfigCompareString,
    ConfigComparison,
    ConfigProcessJson,
    ConfigProcessString,
    compare,
)
from .diff import Difference, DiffStyle
from .directory import ConfigDirectoryTest, run_unittest
from .execution import ConfigRun, ConfigRunValidation, InputMode, OutputMode, execute

VERSION = __version__
