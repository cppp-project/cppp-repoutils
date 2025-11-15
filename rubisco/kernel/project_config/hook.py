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

"""Utils for Rubisco project."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

from rubisco.kernel.command_event.args import (
    Argument,
    DynamicArguments,
    Option,
    load_callback_args,
)
from rubisco.kernel.command_event.callback import EventCallback
from rubisco.kernel.command_event.event_file_data import EventFileData
from rubisco.kernel.command_event.event_path import EventPath
from rubisco.kernel.workflow import (
    parse_workflow_meta,
    run_inline_workflow,
    run_workflow,
)
from rubisco.lib.exceptions import RUValueError
from rubisco.lib.l10n import _
from rubisco.lib.process import Process
from rubisco.lib.typecheck import get_dict_check
from rubisco.lib.variable.fast_format_str import fast_format_str
from rubisco.lib.variable.utils import merge_dict
from rubisco.lib.variable.var_container import VariableContainer

__all__ = ["ProjectHook"]


@dataclass
class ProjectHook:
    """Project hook."""

    raw_data: dict[str, object]
    name: str

    options: list[Option[Any]] = field(default_factory=list, repr=False)  # type: ignore[list]
    args: list[Argument[Any]] | DynamicArguments = field(  # type: ignore[list]
        default_factory=list,
        repr=False,
    )
    description: str = field(default="", repr=False)

    def __post_init__(self) -> None:
        """Parse options and arguments."""
        workflow = cast(
            "str | None",
            get_dict_check(
                self.raw_data,
                "run",
                valtype=str | None,
                default=None,
            ),
        )
        if workflow:
            self.options, self.args, self.description = parse_workflow_meta(
                Path(workflow),
            )
        else:
            self.description = cast(
                "str",
                get_dict_check(
                    self.raw_data,
                    "name",
                    valtype=str,
                    default="",
                ),
            )

    def mount_to_cefs(self, prefix: EventPath | None = None) -> EventPath:
        """Mount this hook to the given event path.

        Args:
            prefix (EventPath | None, optional): The prefix path.
                Defaults to None.

        Returns:
            EventPath: The mounted path.

        """
        if prefix is None:
            prefix = EventPath("/")
        p = prefix / self.name
        p.update_file(
            data=EventFileData(
                args=self.args,
                callbacks=[
                    EventCallback(
                        callback=self.run,
                        description=self.description,
                    ),
                ],
            ),
            description=self.description,
        )

        return p

    def _apply_opts_args(
        self,
        options: list[Option[Any]] | None,
        args: list[Argument[Any]] | None,
    ) -> dict[str, object]:
        opts, args_ = load_callback_args(options or [], args or [])
        opts["args"] = args_

        return opts

    def run(
        self,
        options: list[Option[Any]] | None = None,
        args: list[Argument[Any]] | None = None,
    ) -> None:
        """Run this hook."""
        variables = cast(
            "dict[str, object]",
            get_dict_check(
                self.raw_data,
                "vars",
                valtype=dict[str, object],
                default={},
            ),
        )
        environments = cast(
            "dict[str, str]",
            get_dict_check(
                self.raw_data,
                "env",
                valtype=dict[str, str],
                default={},
            ),
        )
        cmd = cast(
            "str | list[object] | None",
            get_dict_check(
                self.raw_data,
                "exec",
                valtype=str | list | None,
                default=None,
            ),
        )
        workflow = cast(
            "str | None",
            get_dict_check(
                self.raw_data,
                "run",
                valtype=str | None,
                default=None,
            ),
        )
        inline_wf = cast(
            "dict[str, object] | list[dict[str, object]] | None",
            get_dict_check(
                self.raw_data,
                "workflow",
                valtype=dict[str, object] | list[dict[str, object]] | None,
                default=None,
            ),
        )

        # Apply options and arguments.
        opts_args = self._apply_opts_args(options, args)
        variables = variables.copy()
        merge_dict(variables, opts_args)

        # Backup environments before applying.
        environ_bak: dict[str, str | None] = {}
        with VariableContainer(variables):
            # Apply environments to system.
            for key, val in environments.items():
                environ_bak[key] = os.environ.get(key, None)
                os.environ[key] = val

            try:
                # Apply variables to Rubisco.
                with VariableContainer(cast("dict[str, str]", os.environ)):
                    if not cmd and not workflow and not inline_wf:
                        raise RUValueError(
                            fast_format_str(
                                _("Hook '${{name}}' is invalid."),
                                fmt={"name": self.name},
                            ),
                            hint=_(
                                "A workflow [yellow]must[/yellow] contain at "
                                "least 'exec', 'run' or 'workflow'.",
                            ),
                        )

                    # Then, run inline workflow.
                    if inline_wf:
                        run_inline_workflow(inline_wf, self.name)

                    # Then, run workflow.
                    if workflow:
                        run_workflow(Path(workflow))

                    # Finally, execute shell command.
                    if cmd:
                        Process(cmd).run()
            finally:
                for key, val in environ_bak.items():
                    if val is None:
                        del os.environ[key]
                    else:
                        os.environ[key] = val
