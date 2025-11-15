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

"""Workflow support.

Workflow is a ordered list of steps. Each step only contains one action.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, cast

from rubisco.kernel.command_event.args import (
    Argument,
    DynamicArguments,
    Option,
    argument_from_dict,
    option_from_dict,
)
from rubisco.kernel.config_loader import RUConfiguration
from rubisco.kernel.workflow._interfaces import WorkflowInterfaces
from rubisco.kernel.workflow.steps import step_contributes, step_types
from rubisco.kernel.workflow.workflow import Workflow
from rubisco.lib.l10n import _
from rubisco.lib.log import logger
from rubisco.lib.typecheck import get_dict_check
from rubisco.lib.variable.fast_format_str import fast_format_str
from rubisco.shared.ktrigger import IKernelTrigger, call_ktrigger

__all__ = [
    "parse_workflow_meta",
    "register_step_type",
    "run_inline_workflow",
    "run_workflow",
]


def register_step_type(name: str, cls: type, contributes: list[str]) -> None:
    """Register a step type.

    Args:
        name (str): The name of the step type.
        cls (type): The class of the step type.
        contributes (list[str]): The contributes of the step type.

    """
    if name in step_types:
        call_ktrigger(
            IKernelTrigger.on_warning,
            message=fast_format_str(
                _(
                    "Step type '${{name}}' registered multiple times. "
                    "This may cause unexpected behavior. It's unsafe.",
                ),
                fmt={"name": name},
            ),
        )
    step_types[name] = cls
    if cls not in step_contributes:
        step_contributes[cls] = contributes
    logger.info(
        "Step type %s registered with contributes %s",
        name,
        contributes,
    )


def run_inline_workflow(
    data: dict[str, object] | list[dict[str, object]],
    default_id: str,
    *,
    fail_fast: bool = True,
) -> BaseException | None:
    """Run a inline workflow.

    Args:
        data (dict[str, object] | list[dict[str, object]]): Workflow data.
        default_id (str): Default id of the workflow.
        fail_fast (bool, optional): Raise an exception if run failed.
            Defaults to True.

    Returns:
        BaseException | None: If running failed without fail-fast, return its
            exception. Return None if succeed.

    """
    if isinstance(data, list):
        data = {"name": "", "steps": data}

    wf = Workflow(data, default_id)
    try:
        wf.run()
    except BaseException as exc:  # pylint: disable=broad-except
        if fail_fast:
            raise exc from None
        call_ktrigger(
            IKernelTrigger.on_warning,
            message=fast_format_str(
                _(
                    "Workflow running failed: ${{exc}}",
                ),
                fmt={"exc": f"{type(exc).__name__}: {exc}"},
            ),
        )
        return exc
    return None


WorkflowInterfaces.set_run_inline_workflow(run_inline_workflow)


def run_workflow(
    file: Path,
    *,
    fail_fast: bool = True,
    chdir: Path | None = None,
) -> BaseException | None:
    """Run a workflow file.

    Args:
        file (Path): Workflow file path. It can be a JSON, or a yaml.
        fail_fast (bool, optional): Raise an exception if run failed.
            Defaults to True.
        chdir (Path | None, optional): Change working directory to this
            path before running the workflow. Defaults to None.

    Raises:
        RUValueError: If workflow's step parse failed.

    Returns:
        BaseException | None: If running failed without fail-fast, return its
            exception. Return None if succeed.

    """
    cwd = None
    if chdir:
        cwd = Path.cwd()
        os.chdir(chdir)
        call_ktrigger(IKernelTrigger.on_chdir, path=chdir)
    try:
        return run_inline_workflow(
            RUConfiguration.load_from_file(file).config,
            fail_fast=fail_fast,
            default_id=file.stem,
        )
    finally:
        if cwd:
            call_ktrigger(IKernelTrigger.on_leaving_dir, path=chdir)
            os.chdir(cwd)


def parse_workflow_meta(
    file: Path,
) -> tuple[list[Option[Any]], list[Argument[Any]] | DynamicArguments, str]:
    """Parse workflow options and arguments.

    Returns:
        tuple[list[Option[Any]], list[Argument[Any]] | DynamicArguments]:
            The options and arguments and description parsed.

    """
    config = RUConfiguration.load_from_file(file)
    options_json: list[dict[str, object]] = cast(
        "list[dict[str, object]]",
        get_dict_check(
            config.config,
            "options",
            default=[],
            valtype=list[dict[str, object]] | None,
        ),
    )
    options_json.extend(
        cast(
            "list[dict[str, object]]",
            get_dict_check(
                config.config,
                "opts",
                default=[],
                valtype=list[dict[str, object]] | None,
            ),
        ),
    )
    args_json: dict[str, object] | None = cast(
        "dict[str, object] | None",
        get_dict_check(
            config.config,
            "args",
            default=None,
            valtype=dict[str, object] | None,
        ),
    )

    description: str | None = cast(
        "str | None",
        get_dict_check(
            config.config,
            "name",  # Yes, the title of the workflow is the description.
            default="",
            valtype=str | None,
        ),
    )

    options = [option_from_dict(opt_json) for opt_json in options_json]
    args = argument_from_dict(args_json)

    logger.debug(
        "Workflow %s parsed options %s and arguments %s",
        file,
        options,
        args,
    )

    return options, args, description or ""


WorkflowInterfaces.set_run_workflow(run_workflow)
