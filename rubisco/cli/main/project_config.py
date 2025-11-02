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
from typing import TYPE_CHECKING, Any, cast

from rubisco.config import WORKSPACE_REPO_CONFIG
from rubisco.kernel.command_event.callback import EventCallback
from rubisco.kernel.command_event.event_file_data import EventFileData
from rubisco.kernel.command_event.event_path import EventPath
from rubisco.kernel.project_config.project_config import load_project_config
from rubisco.lib.exceptions import RUNotRubiscoProjectError, RUValueError
from rubisco.lib.l10n import _
from rubisco.lib.log import logger
from rubisco.lib.variable.fast_format_str import fast_format_str
from rubisco.lib.variable.utils import make_pretty

if TYPE_CHECKING:
    from rubisco.kernel.command_event.args import Argument, Option
    from rubisco.kernel.project_config.hook import ProjectHook
    from rubisco.kernel.project_config.project_config import ProjectConfigration

__all__ = [
    "bind_hook",
    "call_hook",
    "get_hooks",
    "get_project_config",
    "load_project",
]


_hooks: dict[str, list[ProjectHook]] = {}

_project_config: ProjectConfigration | None = None


def get_hooks() -> dict[str, list[ProjectHook]]:
    """Get all hooks.

    Returns:
        dict[str, list]: The hooks.

    """
    return _hooks


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


def _add_hook_to_cefs(path: EventPath, name: str) -> None:
    # TODO(ChenPi11, #0): Use CEFS to manage hook callbacks.  # noqa: FIX002
    def _callback(
        options: list[Option[Any]],  # noqa: ARG001 # pylint: disable=W0613
        args: list[Argument[Any]],  # noqa: ARG001 # pylint: disable=W0613
    ) -> None:
        call_hook(name)

    path /= name
    path.update_file(
        EventFileData(
            args=[],
            callbacks=[EventCallback(callback=_callback, description="")],
        ),
    )


def bind_hook(name: str) -> None:
    """Bind hook to a command.

    Args:
        name (str): Hook name.

    """
    logger.debug("Binding hook: %s", name)
    if _project_config and name in _project_config.hooks:
        if name not in _hooks:
            _hooks[name] = []
        _hooks[name].append(cast("ProjectHook", _project_config.hooks[name]))
        _add_hook_to_cefs(EventPath("/"), name)


def call_hook(name: str) -> None:
    """Call a hook.

    Args:
        name (str): The hook name.

    """
    if name not in _hooks:
        raise RUValueError(
            fast_format_str(
                _("Undefined command or hook ${{name}}."),
                fmt={"name": name},
            ),
            hint=_("Perhaps a typo?"),
        )
    for hook in _hooks[name]:
        hook.run()


def load_project() -> None:
    """Load the project in cwd."""
    global _project_config  # pylint: disable=global-statement # noqa: PLW0603
    try:
        _project_config = load_project_config(Path.cwd())
        for hook_name in _project_config.hooks:  # Bind all hooks.
            bind_hook(hook_name)
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
