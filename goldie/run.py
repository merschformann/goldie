import subprocess
import tempfile
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


def run(
    input_file: str,
    configuration: ConfigRun,
) -> tuple[int, str]:
    """
    Run the command with the input file and return the result.

    Parameters
    ----------
    input_file : str
        The file to read the input from.
    configuration : ConfigRun
        The configuration for running the command.

    Returns
    -------
    tuple[int, str]
        The exit code and the path to the file to which the output was written.
    """
    # Create temporary files for input and output
    with tempfile.NamedTemporaryFile("w+") as input, tempfile.NamedTemporaryFile("w+") as output:
        # Write the input to the temporary file
        with open(input_file, "r") as f:
            input.write(f.read())
            input.seek(0)

        # Replace the placeholders in the arguments
        args = [arg.format(input=input.name, output=output.name) for arg in configuration.args]

        # Run the command
        with open(output.name, "w") as f:
            process = subprocess.run(
                [configuration.cmd, *args],
                stdin=input if configuration.input_mode == InputMode.STDIN else None,
                stdout=f if configuration.output_mode in [OutputMode.STDOUT, OutputMode.BOTH] else None,
                stderr=f if configuration.output_mode in [OutputMode.STDERR, OutputMode.BOTH] else None,
            )

        # Return the exit code and the path to the output file
        return process.returncode, output.name
