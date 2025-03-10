from .__about__ import __version__
from .compare import (
    ConfigCompareJson,
    ConfigCompareString,
    ConfigComparison,
    ConfigProcessJson,
    ConfigProcessString,
    compare,
)
from .diff import Difference, DiffStyle
from .directory import ConfigDirectoryTest, run_unittest
from .run import ConfigRun, ConfigRunValidation, InputMode, OutputMode, run

VERSION = __version__
