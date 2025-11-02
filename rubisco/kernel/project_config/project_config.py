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

"""Project configuration loader."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from beartype import beartype

from rubisco.config import APP_VERSION, WORKSPACE_REPO_CONFIG
from rubisco.kernel.config_loader import RUConfiguration
from rubisco.kernel.project_config.hook import ProjectHook
from rubisco.kernel.project_config.maintainer import Maintainer
from rubisco.lib.exceptions import (
    RUNotRubiscoProjectError,
    RUValueError,
)
from rubisco.lib.l10n import _
from rubisco.lib.log import logger
from rubisco.lib.typecheck import get_dict_check
from rubisco.lib.variable.fast_format_str import fast_format_str
from rubisco.lib.variable.format import format_auto, format_str
from rubisco.lib.variable.utils import make_pretty
from rubisco.lib.variable.variable import pop_variables, push_variables
from rubisco.lib.version import Version

__all__ = [
    "ProjectConfigration",
    "load_project_config",
]


class ProjectConfigration:  # pylint: disable=too-many-instance-attributes
    """Project configuration instance."""

    config: RUConfiguration

    # Project mandatory configurations.
    name: str
    version: Version

    # Project optional configurations.
    description: str
    rubisco_min_version: Version
    maintainers: list[Maintainer] | Maintainer
    license: str | None
    hooks: dict[str, object]

    pushed_variables: list[str]

    def __init__(self, config_file: Path) -> None:
        """Initialize the project configuration."""
        self.hooks = {}
        self.pushed_variables = []

        if not config_file.is_file():
            logger.warning(
                "The project configuration file '%s' is not found.",
                config_file,
            )
            raise RUNotRubiscoProjectError(
                fast_format_str(
                    _("Project configuration file '${{path}}' is not found."),
                    fmt={
                        "path": make_pretty(config_file),
                    },
                ),
            )

        self.config = RUConfiguration.load_from_file(config_file)

        self._load()

    def _check_version(self) -> None:
        if self.rubisco_min_version > APP_VERSION:
            raise RUValueError(
                fast_format_str(
                    _(
                        "The minimum version of rubisco required by the "
                        "project [underline][link=${{uri}}]${{name}}[/link]"
                        "[/underline]' is '[cyan]${{version}}[/cyan]'.",
                    ),
                    fmt={
                        "uri": self.config.path.as_uri(),
                        "name": make_pretty(self.name, _("<Unnamed>")),
                        "version": str(self.rubisco_min_version),
                    },
                ),
                hint=_("Please upgrade Rubisco to the required version."),
            )

    def _load(self) -> None:
        self.name = str(get_dict_check(self.config.config, "name", valtype=str))
        self.version = Version(
            str(get_dict_check(self.config.config, "version", valtype=str)),
        )
        self.description = str(
            format_str(
                get_dict_check(
                    self.config.config,
                    "description",
                    valtype=str,
                    default="",
                ),
            ),
        )

        self.rubisco_min_version = Version(
            str(
                get_dict_check(
                    self.config.config,
                    "rubisco-min-version",
                    valtype=str,
                    default="0.0.0",
                ),
            ),
        )

        self._check_version()

        _m = cast(
            "str | None",
            get_dict_check(
                self.config.config,
                "maintainer",
                default=None,
                valtype=str | None,
            ),
        )
        if _m:
            maintainer = Maintainer.parse(_m)
            self.maintainers = [maintainer]
        else:
            self.maintainers = []

        _ms = cast(
            "list[str] | list[dict[str, str | None]] | None",
            get_dict_check(
                self.config.config,
                "maintainers",
                default=None,
                valtype=list[str] | list[dict[str, str | None]] | None,
            ),
        )
        if _ms:
            self.maintainers.extend([Maintainer.parse(x) for x in _ms])

        self.license = cast(
            "str | None",
            get_dict_check(
                self.config.config,
                "license",
                default=None,
                valtype=str | None,
            ),
        )

        # Only hooks supported format.
        hooks = cast(
            "dict[str, dict[str, object]]",
            format_auto(
                get_dict_check(
                    self.config.config,
                    "hooks",
                    default={},
                    valtype=dict,
                ),
            ),
        )

        # TODO(ChenPi11): Use CEFS.  # noqa: FIX002, TD003
        for name, data in hooks.items():
            self.hooks[name] = ProjectHook(
                data,  # type: ignore[assignment]
                name,
            )

        # Serialize configuration to variables.
        def _push_vars(
            obj: dict[str, object] | list[object] | object,
            prefix: str,
        ) -> None:
            if isinstance(obj, dict):
                for key, value in cast("dict[str, object]", obj).items():
                    self.pushed_variables.append(f"{prefix}.{key}")
                    push_variables(f"{prefix}.{key}", value)
                    _push_vars(value, f"{prefix}.{key}")
            elif isinstance(obj, list):
                self.pushed_variables.append(f"{prefix}.length")
                push_variables(
                    f"{prefix}.length",
                    len(cast("list[object]", obj)),
                )
                for idx, val in enumerate(cast("list[object]", obj)):
                    _push_vars(val, f"{prefix}.{idx}")
            else:
                self.pushed_variables.append(prefix)
                push_variables(prefix, obj)

        _push_vars(self.config.config, "project")

    def __repr__(self) -> str:
        """Get the string representation of the project configuration.

        Returns:
            str: The string representation of the project configuration.

        """
        return f"<ProjectConfiguration: {self.name} {self.version}>"

    def run_hook(self, name: str) -> None:
        """Run a hook by its name.

        Args:
            name (str): The hook name.

        """
        cast("ProjectHook", self.hooks[name]).run()

    def __del__(self) -> None:
        """Remove all pushed variables."""
        for val in self.pushed_variables:
            pop_variables(val)


@beartype
def load_project_config(project_dir: Path) -> ProjectConfigration:
    """Load the project configuration from the given configuration file.

    Args:
        project_dir (Path): The path to the project configuration file.

    Returns:
        ProjectConfigration: The project configuration instance.

    """
    return ProjectConfigration(project_dir / WORKSPACE_REPO_CONFIG)


_T = Path  # Make Ruff happy.
