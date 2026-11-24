"""Skip generated files that already exist."""

from argparse import ArgumentParser
from pathlib import Path


def add_force_argument(parser: ArgumentParser) -> None:
    """Add --force to a script that writes generated files."""
    parser.add_argument("--force", action="store_true", help="Overwrite existing outputs")


def outputs_exist(paths, force: bool = False) -> bool:
    """True when every output exists and the caller did not ask to rebuild."""
    if isinstance(paths, (str, Path)):
        paths = [paths]
    return not force and all(Path(path).exists() for path in paths)
