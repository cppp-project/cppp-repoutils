# -*- coding: utf-8 -*-
# -*- mode: python -*-
# vi: set ft=python :

# Copyright (C) 2024 The C++ Plus Project.
# This file is part of the repoutils.
#
# repoutils is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 3 of the License,
# or (at your option) any later version.
#
# repoutils is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Project configuration loader.
"""

from pathlib import Path

import json5 as json

from repoutils.config import APP_VERSION, USER_REPO_CONFIG
from repoutils.kernel.workflow import run_inline_workflow, run_workflow
from repoutils.lib.exceptions import RUValueException
from repoutils.lib.fileutil import glob_path, resolve_path
from repoutils.lib.l10n import _
from repoutils.lib.process import Process
from repoutils.lib.variable import (AutoFormatDict, format_str, make_pretty,
                                    pop_variables, push_variables)
from repoutils.lib.version import Version

__all__ = [
    "ProjectConfigration",
    "ProjectHook",
    "load_project_config",
]


class ProjectHook:  # pylint: disable=too-few-public-methods
    """
    Project hook.
    """

    _raw_data: AutoFormatDict
    name: str

    def __init__(self, data: AutoFormatDict, name: str):
        self._raw_data = data
        self.name = name

    def run(self):
        """
        Run this hook.
        """
        variables: AutoFormatDict = self._raw_data.get(
            "vars",
            {},
            valtype=dict,
        )
        try:
            for name, val in variables.items():  # Push all variables first.
                push_variables(name, val)

            cmd = self._raw_data.get("exec", None, valtype=str | list | None)
            workflow = self._raw_data.get("run", None, valtype=str | None)
            inline_wf = self._raw_data.get(
                "workflow",
                None,
                valtype=dict | AutoFormatDict | list | None,
            )

            if not cmd and not workflow and not inline_wf:
                raise RUValueException(
                    format_str(
                        _("Hook '${{name}}' is invalid."),
                        fmt={"name": make_pretty(self.name)},
                    ),
                    hint=_(
                        "A workflow [yellow]SHOULD[/yellow] contain at "
                        "least 'exec', 'run' and 'workflow'."
                    ),
                )

            # Then, run inline workflow.
            if inline_wf:
                run_inline_workflow(inline_wf)

            # Then, run workflow.
            if workflow:
                run_workflow(Path(workflow))

            # Finally, execute shell command.
            if cmd:
                Process(cmd).run()
        finally:
            for name in variables.keys():
                pop_variables(name)


class ProjectConfigration:  # pylint: disable=too-many-instance-attributes
    """
    Project configuration instance.
    """

    config_file: Path
    config: AutoFormatDict

    # Project mandatory configurations.
    name: str
    version: Version

    # Project optional configurations.
    description: str
    repoutils_min_version: Version
    maintainer: list[str] | str
    license: str
    hooks: AutoFormatDict

    def __init__(self, config_file: Path):
        self.config_file = config_file
        self.config = AutoFormatDict()
        self.hooks = AutoFormatDict()

        self._load()

    def _load(self):
        with self.config_file.open() as file:
            self.config = AutoFormatDict.from_dict(json.load(file))

        self.name = self.config.get("name", valtype=str)
        self.version = Version(self.config.get("version", valtype=str))
        self.description = self.config.get(
            "description",
            default="",
            valtype=str,
        )

        self.repoutils_min_version = Version(
            self.config.get("repoutils-min-version", "0.0.0", valtype=str)
        )

        if self.repoutils_min_version > APP_VERSION:
            raise RUValueException(
                format_str(
                    _(
                        "The minimum version of repoutils required by the project "  # noqa: E501
                        "'[underline]${{name}}[/underline]' is "
                        "'[underline]${{version}}[/underline]'."
                    ),
                    fmt={
                        "name": make_pretty(self.name, _("<Unnamed>")),
                        "version": self.repoutils_min_version,
                    },
                ),
                hint=_("Please upgrade repoutils to the required version."),
            )

        self.maintainer = self.config.get(
            "maintainer",
            default=_("[yellow]Unknown[/yellow]"),
            valtype=list | str,
        )

        self.license = self.config.get(
            "license",
            default=_("[yellow]Unknown[/yellow]"),
            valtype=str,
        )

        hooks = self.config.get("hooks", default={}, valtype=dict)
        for name, data in hooks.items():
            self.hooks[name] = ProjectHook(data, name)

    def __repr__(self) -> str:
        """Get the string representation of the project configuration.

        Returns:
            str: The string representation of the project configuration.
        """

        return f"<ProjectConfiguration: {self.name} {self.version}>"

    def __str__(self) -> str:
        """Get the string representation of the project configuration.

        Returns:
            str: The string representation of the project configuration.
        """

        return repr(self)

    def run_hook(self, name: str):
        """Run a hook by its name.

        Args:
            name (str): The hook name.
        """

        self.hooks[name].run()


def _load_config(config_file: Path, loaded_list: list[Path]) -> AutoFormatDict:
    config_file = config_file.resolve()
    with config_file.open() as file:
        config = AutoFormatDict.from_dict(json.load(file))
        if not isinstance(config, AutoFormatDict):
            raise RUValueException(
                format_str(
                    _(
                        "Invalid configuration in file "
                        "'[underline]${{path}}[/underline]'."
                    ),
                    fmt={"path": make_pretty(config_file.absolute())},
                ),
                hint=_("Configuration must be a JSON5 object. (dict)"),
            )
        for include in config.get("includes", [], valtype=list):
            if not isinstance(include, str):
                raise RUValueException(
                    format_str(
                        _(
                            "Invalid path in '[underline]${{path}}[/underline]'."  # noqa: E501
                        ),
                        fmt={"path": make_pretty(config_file.absolute())},
                    )
                )
            include_file = config_file.parent / include
            if include_file.is_dir():
                include_file = include_file / USER_REPO_CONFIG
            include_file = resolve_path(include_file)
            for one_file in glob_path(include_file):
                if one_file in loaded_list:  # Avoid circular dependencies.
                    continue  # Skip already loaded files.
                loaded_list.append(one_file)

            config.merge(_load_config(include_file, loaded_list))

    return config


def load_project_config(project_dir: Path) -> ProjectConfigration:
    """Load the project configuration from the given configuration file.

    Args:
        project_dir (Path): The path to the project configuration file.

    Returns:
        ProjectConfigration: The project configuration instance.
    """

    return ProjectConfigration(project_dir / USER_REPO_CONFIG)


if __name__ == "__main__":
    import rich

    rich.print(f"{__file__}: {__doc__.strip()}")

    rich.print(_load_config(Path("project.json"), []))
