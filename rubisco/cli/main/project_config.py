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

"""C++ Plus Rubisco CLI hook utils."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from rubisco.config import WORKSPACE_REPO_CONFIG
from rubisco.kernel.project_config.project_config import load_project_config
from rubisco.lib.exceptions import RUNotRubiscoProjectError
from rubisco.lib.l10n import _
from rubisco.lib.variable.fast_format_str import fast_format_str
from rubisco.lib.variable.utils import make_pretty

if TYPE_CHECKING:
    from rubisco.kernel.project_config.project_config import ProjectConfigration

__all__ = [
    "get_project_config",
    "load_project",
]

_project_config: ProjectConfigration | None = None  # pylint: disable=C0103


def get_project_config() -> ProjectConfigration | None:
    """Get the project config.

    Returns:
        ProjectConfigration | None: The project config.

    """
    if _project_config is None:
        raise RUNotRubiscoProjectError(
            fast_format_str(
                _(
                    "Working directory ${{path}} is not a Rubisco project.",
                ),
                fmt={"path": make_pretty(Path.cwd().absolute())},
            ),
        )
    return _project_config


def load_project() -> None:
    """Load the project in cwd."""
    global _project_config  # pylint: disable=global-statement # noqa: PLW0603
    try:
        _project_config = load_project_config(Path.cwd())
        _project_config.mount_to_cefs()
    except RUNotRubiscoProjectError as exc:
        raise RUNotRubiscoProjectError(
            fast_format_str(
                _(
                    "Working directory ${{path}} is not a Rubisco project.",
                ),
                fmt={"path": make_pretty(Path.cwd().absolute())},
            ),
            hint=fast_format_str(
                _("${{path}} is not found."),
                fmt={"path": make_pretty(WORKSPACE_REPO_CONFIG.absolute())},
            ),
        ) from exc
