import subprocess
import tempfile
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
        The file to read the input from.
    output_file : str
        The file to write the output to.
    configuration : Configuration
        The configuration for running the command.
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
        with open(output_file, "w") as f:
            process = subprocess.run(
                [configuration.cmd, *args],
                stdin=input if configuration.use_stdin else None,
                stdout=f if configuration.use_stdout else None,
                stderr=f if configuration.output_mode == OutputMode.STDERR else None,
            )

        # Read the output from the temporary file
        output.seek(0)
        return output.read()
