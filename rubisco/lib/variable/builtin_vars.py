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

"""Rubisco built-in variables."""

import os
import platform
import shutil
import sys
from pathlib import Path

from rubisco.config import APP_VERSION, RUBISCO_COMMAND
from rubisco.lib.variable.variable import push_variables

__all__ = ["init_builtin_vars"]


def init_builtin_vars() -> None:
    """Initialize the built-in variables."""
    uname_result = platform.uname()
    push_variables("home", str(Path.home().absolute()))
    push_variables("nproc", os.cpu_count())
    push_variables("rubisco", str(RUBISCO_COMMAND))
    push_variables("rubisco.version", str(APP_VERSION))
    push_variables("rubisco.python_version", sys.version)
    push_variables("rubisco.python_impl", sys.implementation.name)
    push_variables("host", os.name)
    push_variables("host.system", uname_result.system)
    push_variables("host.node", uname_result.node)
    push_variables("host.release", uname_result.release)
    push_variables("host.version", uname_result.version)
    push_variables("host.machine", uname_result.machine)
    push_variables("host.processor", uname_result.processor)
    push_variables("python.executable", sys.executable)
    push_variables("python.version", platform.python_version())
    push_variables("python.impl", platform.python_implementation())
    if shutil.which("python"):
        push_variables("python", "python")
    else:
        push_variables("python", "python3")
