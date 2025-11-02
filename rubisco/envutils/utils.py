# -*- mode: python -*-
# vi: set ft=python :

# Copyright (C) 2024-2025 The C++ Plus Project.
# This file is part of the Rubisco.
#
# Rubisco is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 3 of the License,
# or (at your option) any later version.
#
# Rubisco is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Package management utils for environment."""

import os
import sys
from pathlib import Path

from rubisco.lib.l10n import _
from rubisco.lib.variable.fast_format_str import fast_format_str
from rubisco.lib.variable.utils import make_pretty
from rubisco.shared.ktrigger import IKernelTrigger, call_ktrigger

__all__ = ["add_venv_to_syspath", "canonical_pkg_name", "is_venv"]


def is_venv(path: Path) -> bool:
    """Check if a path is a Python virtual environment.

    Args:
        path (Path): Path to check.

    Returns:
        bool: True if the path is a Python virtual environment,
              otherwise False.

    """
    if not path.exists():
        return False

    if not path.is_dir():
        return False

    return (path / "pyvenv.cfg").is_file()


def add_venv_to_syspath(path: Path) -> None:
    """Add a venv to sys.path.

    Args:
        path (Path): The path to add.

    """
    if not is_venv(path):
        return

    try:
        if os.name == "nt":
            sys.path.append(str(path / "Lib"))
            sys.path.append(str(path / "Lib" / "site-packages"))
        else:
            sys.path.append(str(path / "lib"))
            libs = (path / "lib").iterdir()
            for lib in libs:
                if lib.is_dir() and lib.name.startswith("python"):
                    sys.path.append(str(lib))
                    sys.path.append(str(lib / "site-packages"))
    except OSError as exc:
        call_ktrigger(
            IKernelTrigger.on_warning,
            message=fast_format_str(
                _("Failed to add ${{path}} to sys.path: ${{exc}}"),
                fmt={"path": make_pretty(path), "exc": str(exc)},
            ),
        )


def canonical_pkg_name(pkg_name: str) -> str:
    """Canonicalize the package name.

    Args:
        pkg_name (str): The package name.

    Returns:
        str: The canonicalized package name.

    """
    return pkg_name.replace("-", "_")
