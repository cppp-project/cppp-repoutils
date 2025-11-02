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

"""Rubisco extension API for `rubisco.kernel` (without CommandEventFS).

The CEFS is too complex. Although it is a part of Rubisco kernel. but I will put
it into `rubisco.shared.api.cefs`.
"""

from rubisco.kernel.config_file import config_file
from rubisco.kernel.config_loader import RUConfiguration
from rubisco.kernel.ext_name_check import is_valid_extension_name
from rubisco.kernel.mirrorlist import get_url as get_mirror_url
from rubisco.kernel.project_config.hook import ProjectHook
from rubisco.kernel.project_config.maintainer import Maintainer
from rubisco.kernel.project_config.project_config import (
    ProjectConfigration,
    load_project_config,
)
from rubisco.kernel.project_config.utils import is_rubisco_project
from rubisco.kernel.workflow.step import Step
from rubisco.kernel.workflow.workflow import Workflow

__all__ = [
    "Maintainer",
    "ProjectConfigration",
    "ProjectHook",
    "RUConfiguration",
    "Step",
    "Workflow",
    "get_mirror_url",
    "get_rubisco_configuration",
    "is_rubisco_project",
    "is_valid_extension_name",
    "load_project_config",
]


def get_rubisco_configuration() -> RUConfiguration:
    """Get the Rubisco configuration.

    Returns:
        RUConfiguration: The Rubisco configuration.

    """
    return config_file
