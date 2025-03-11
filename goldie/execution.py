import subprocess
from dataclasses import dataclass
from enum import Enum


class InputMode(Enum):
    STDIN = "stdin"
    """Feeds the input file via stdin."""
    NONE = "none"
    """Does not feed anything to the stdin."""


class OutputMode(Enum):
    STDOUT = "stdout"
    """Intercepts only stdout."""
    STDERR = "stderr"
    """Intercepts only stderr."""
    BOTH = "both"
    """Intercepts both stdout and stderr."""
    NONE = "none"
    """Does not intercept anything, i.e., ignores the output."""


@dataclass
class ConfigRun:
    """Configuration for running a command."""

    cmd: str
    """The command to run."""
    args: list[str]
    """
    The arguments to pass to the command.
    If the path to the input file is needed (instead of feeding via stdin), use the string "{input}".
    If the path to the output file is needed (instead of reading stdout), use the string "{output}".
    """
    input_mode: InputMode = InputMode.STDIN
    """The input mode."""
    output_mode: OutputMode = OutputMode.STDOUT
    """The output mode."""


@dataclass
class ConfigRunValidation:
    """Configuration for validating the command"""

    validate_exit_code: bool = True
    """Whether to validate the exit code of the command."""
    expected_exit_code: int = 0
    """The desired exit code of the command."""


def execute(
    input_file: str,
    output_file: str,
    cwd: str,
    configuration: ConfigRun,
) -> int:
    """
    Run the command with the input file and return the result.

    Parameters
    ----------
    input_file : str
        The file to read the input from.
    output_file : str
        The file to write the output to.
    cwd : str
        The directory to run the command in.
    configuration : ConfigRun
        The configuration for running the command.

    Returns
    -------
    int
        The exit code of the command.
    """
    # Replace the placeholders in the arguments
    args = [arg.format(input=input_file, output=output_file) for arg in configuration.args]

    # Run the command
    with open(output_file, "w") as f:
        input_file = None if configuration.input_mode == InputMode.NONE else open(input_file)
        process = subprocess.run(
            [configuration.cmd, *args],
            stdin=input_file if configuration.input_mode == InputMode.STDIN else None,
            stdout=f if configuration.output_mode in [OutputMode.STDOUT, OutputMode.BOTH] else None,
            stderr=f if configuration.output_mode in [OutputMode.STDERR, OutputMode.BOTH] else None,
            cwd=cwd,
        )

    # Close the input file if necessary
    if input_file is not None:
        input_file.close()

    # Return the exit code and the path to the output file
    return process.returncode
