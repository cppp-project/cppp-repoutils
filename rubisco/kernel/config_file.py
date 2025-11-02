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

"""Rubisco config file."""

from pathlib import Path

from rubisco.config import (
    GLOBAL_CONFIG_FILE,
    USER_CONFIG_FILE,
    WORKSPACE_CONFIG_FILE,
)
from rubisco.kernel.config_loader import RUConfiguration
from rubisco.lib.log import logger

__all__ = ["config_file"]


config_file = RUConfiguration()


def _load_json(file: Path, envname: str) -> None:
    try:
        if file.exists():
            config_file.path = file
            config_file.merge(RUConfiguration.load_from_file(file))
    except OSError:
        logger.warning(
            "Failed to load %s configuration: %s",
            envname,
            file,
            exc_info=True,
        )


_load_json(GLOBAL_CONFIG_FILE, "global")
_load_json(USER_CONFIG_FILE, "user")
_load_json(WORKSPACE_CONFIG_FILE, "workspace")
