from dataclasses import dataclass
from enum import Enum


class OutputMode(Enum):
    STDOUT = "stdout"
    """Intercepts only stdout."""
    STDERR = "stderr"
    """Intercepts only stderr."""
    BOTH = "both"
    """Intercepts both stdout and stderr."""


@dataclass
class Configuration:
    cmd: str
    """The command to run."""
    args: list[str]
    """
    The arguments to pass to the command.
    If the path to the input file is needed (instead of feeding via stdin), use the string "{input}".
    If the path to the output file is needed (instead of reading stdout), use the string "{output}".
    """
    use_stdin: bool = True
    """Whether to use stdin for input."""
    use_stdout: bool = True
    """Whether to use stdout for output."""
    output_mode: OutputMode = OutputMode.STDOUT
    """Indicates how to intercept the output."""


def run(
    input_file: str,
    output_file: str,
    configuration: Configuration,
):
    """
    Run the command with the input file and write the output to the output file.

    Parameters
    ----------
    input_file : str
        The path to the input file.
    output_file : str
        The path to the output file.
    configuration : Configuration
        The configuration for running the command.
    """
    pass
