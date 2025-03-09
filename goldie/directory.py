from dataclasses import dataclass


@dataclass
class Configuration:
    """Configuration for directory based golden file testing."""

    directory: str
    file_filter: str
