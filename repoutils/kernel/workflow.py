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
Workflow support.
Workflow is a ordered list of steps. Each step only contains one action.
"""

import os
import uuid
from pathlib import Path

import json5 as json
import yaml

from repoutils.config import DEFAULT_CHARSET
from repoutils.lib.exceptions import RUValueException
from repoutils.lib.fileutil import copy_recursive, rm_recursive
from repoutils.lib.l10n import _
from repoutils.lib.log import logger
from repoutils.lib.process import Process, popen
from repoutils.lib.variable import (AutoFormatDict, format_str, make_pretty,
                                    push_variables)
from repoutils.shared.ktrigger import IKernelTrigger, call_ktrigger

__all__ = [
    "Step",
    "ShellExecStep",
    "MkdirStep",
    "PopenStep",
    "OutputStep",
    "MoveFileStep",
    "CopyFileStep",
    "RemoveStep",
    "Workflow",
    "register_step_type",
    "run_inline_workflow",
    "run_workflow",
    "_set_extloader",
]

try:  # Avoid circular import.
    from repoutils.shared.extention import load_extention
except ImportError:
    load_extention = NotImplemented


def _set_extloader(extloader):
    global load_extention  # pylint: disable=global-statement

    load_extention = extloader


class Step:
    """A step in the workflow."""

    id: str
    par_workflow: "Workflow"
    name: str
    desc: str
    next: "Step | None"
    raw_data: AutoFormatDict
    global_id: str

    def __init__(self, data: AutoFormatDict, par_workflow: "Workflow"):
        """Create a new step.

        Args:
            data (AutoFormatDict): The step json data.
            par_workflow (Workflow): The parent workflow.
        """

        self.par_workflow = par_workflow
        self.raw_data = data
        self.name = data.get("name", valtype=str, default="")
        self.desc = data.get("desc", valtype=str, default="")
        self.next = None
        self.id = data.get("id", valtype=str)  # Always exists.
        self.global_id = f"{self.par_workflow.id}.{self.id}"

        call_ktrigger(
            IKernelTrigger.pre_run_workflow_step,
            step=self,
        )

    def __str__(self):
        """Return the name of the step.

        Returns:
            str: The name of the step.
        """

        return self.name

    def __repr__(self):
        """Return the representation of the step.

        Returns:
            str: The repr of the step.
        """

        return f"<{self.__class__.__name__} {self.name}>"


# Built-in step types.
class ShellExecStep(Step):  # pylint: disable=too-few-public-methods
    """A shell execution step."""

    cmd: str
    cwd: Path
    fail_on_error: bool

    def __init__(self, data: AutoFormatDict, par_workflow: "Workflow"):
        self.cmd = data.get("run", valtype=str)

        self.cwd = Path(data.get("cwd", valtype=str, default=""))
        self.fail_on_error = data.get(
            "fail-on-error",
            valtype=bool,
            default=True,
        )
        super().__init__(data, par_workflow)

        retcode = Process(self.cmd, self.cwd).run(self.fail_on_error)
        push_variables(f"{self.global_id}.retcode", retcode)


class MkdirStep(Step):  # pylint: disable=too-few-public-methods
    """Make directories."""

    path: Path

    def __init__(self, data: AutoFormatDict, par_workflow: "Workflow"):
        self.path = Path(data.get("mkdir", valtype=str))
        super().__init__(data, par_workflow)

        call_ktrigger(IKernelTrigger.on_mkdir, path=self.path)
        os.makedirs(self.path, exist_ok=True)


class PopenStep(Step):  # pylint: disable=too-few-public-methods
    """A popen step."""

    cmd: str
    cwd: Path
    fail_on_error: bool
    stdout: bool
    stderr: int

    def __init__(self, data: AutoFormatDict, par_workflow: "Workflow"):
        self.cmd = data.get("popen", valtype=str)

        self.cwd = Path(data.get("cwd", valtype=str, default=""))
        self.fail_on_error = data.get(
            "fail-on-error",
            valtype=bool,
            default=True,
        )
        self.stdout = data.get("stdout", valtype=bool, default=True)
        stderr_mode = data.get("stderr", valtype=bool | str, default=True)
        if stderr_mode is True:
            self.stderr = 1
        elif stderr_mode is False:
            self.stderr = 0
        else:
            self.stderr = 2

        super().__init__(data, par_workflow)

        stdout, stderr, retcode = popen(
            self.cmd, self.cwd, self.stdout, self.stderr, self.fail_on_error
        )
        push_variables(f"{self.global_id}.stdout", stdout)
        push_variables(f"{self.global_id}.stderr", stderr)
        push_variables(f"{self.global_id}.retcode", retcode)


class OutputStep(Step):  # pylint: disable=too-few-public-methods
    """Output a message."""

    msg: str

    def __init__(self, data: AutoFormatDict, par_workflow: "Workflow"):
        self.msg = str(data.get("output"))

        super().__init__(data, par_workflow)

        call_ktrigger(IKernelTrigger.on_output, msg=self.msg)


class MoveFileStep(Step):  # pylint: disable=too-few-public-methods
    """Move a file."""

    src: Path
    dst: Path

    def __init__(self, data: AutoFormatDict, par_workflow: "Workflow"):
        self.src = Path(data.get("move", valtype=str))
        self.dst = Path(data.get("to", valtype=str))

        super().__init__(data, par_workflow)

        call_ktrigger(IKernelTrigger.on_move_file, src=self.src, dst=self.dst)
        os.rename(self.src, self.dst)


class CopyFileStep(Step):  # pylint: disable=too-few-public-methods
    """Copy a file."""

    src: Path
    dst: Path
    strict: bool
    keep_symlinks: bool
    excludes: list[str] | None

    def __init__(self, data: AutoFormatDict, par_workflow: "Workflow"):
        self.src = Path(data.get("copy", valtype=str))
        self.dst = Path(data.get("to", valtype=str))

        self.strict = data.get("strict", valtype=bool, default=True)
        self.keep_symlinks = data.get(
            "keep-symlinks",
            valtype=bool,
            default=False,
        )
        self.excludes = data.get(
            "excludes",
            valtype=list | None,
            default=None,
        )

        super().__init__(data, par_workflow)

        call_ktrigger(IKernelTrigger.on_copy, src=self.src, dst=self.dst)
        copy_recursive(
            self.src,
            self.dst,
            self.strict,
            self.keep_symlinks,
            not self.strict,
            self.excludes,
        )


class RemoveStep(Step):  # pylint: disable=too-few-public-methods
    """
    Remove a file or directory.
    This step is dangerous. Use it with caution!
    """

    paths: list[Path]
    strict: bool

    def __init__(self, data: AutoFormatDict, par_workflow: "Workflow"):
        remove = data.get("remove", valtype=str | list)
        if isinstance(remove, str):
            self.paths = [Path(remove)]
        else:
            for item in remove:
                if not isinstance(item, str):
                    raise RUValueException(
                        _("The remove item must be a string."),
                    )
            self.paths = [Path(item) for item in remove]

        self.strict = data.get("strict", valtype=bool, default=True)

        super().__init__(data, par_workflow)

        for path in self.paths:
            call_ktrigger(IKernelTrigger.on_remove, path=path)
            rm_recursive(path, self.strict)


class ExtentionLoadStep(Step):  # pylint: disable=too-few-public-methods
    """
    Load a Repoutils Excention manually.
    """

    path: Path
    strict: bool

    def __init__(self, data: AutoFormatDict, par_workflow: "Workflow"):
        self.path = Path(data.get("extention", valtype=str))

        self.strict = data.get("strict", valtype=bool, default=True)

        super().__init__(data, par_workflow)

        load_extention(self.path, self.strict)


class WorkflowRunStep(Step):  # pylint: disable=too-few-public-methods
    """
    Run another workflow.
    """

    path: Path
    fail_fast: bool

    def __init__(self, data: AutoFormatDict, par_workflow: "Workflow"):
        self.path = Path(data.get("workflow", valtype=str))

        self.fail_fast = data.get("fail-fast", valtype=bool, default=True)

        super().__init__(data, par_workflow)

        exc = run_workflow(self.path, self.fail_fast)
        if exc:
            push_variables(f"{self.global_id}.exception", exc)


step_types = {
    "shell": ShellExecStep,
    "mkdir": MkdirStep,
    "output": OutputStep,
    "popen": PopenStep,
    "move": MoveFileStep,
    "copy": CopyFileStep,
    "remove": RemoveStep,
    "load-extention": ExtentionLoadStep,
    "run-workflow": WorkflowRunStep,
}

# Type is optional. If not provided, it will be inferred from the step data.
step_contribute = {
    ShellExecStep: ["run"],
    MkdirStep: ["mkdir"],
    PopenStep: ["popen"],
    OutputStep: ["output"],
    MoveFileStep: ["move", "to"],
    CopyFileStep: ["copy", "to"],
    RemoveStep: ["remove"],
    ExtentionLoadStep: ["extention"],
    WorkflowRunStep: ["workflow"],
}


class Workflow:
    """A workflow."""

    id: str
    name: str
    first_step: Step
    raw_data: AutoFormatDict

    def __init__(self, data: AutoFormatDict) -> None:
        """Create a new workflow.

        Args:
            data (AutoFormatDict): The workflow json data.
        """

        self.id = data.get(
            "id",
            valtype=str,
            default=str(uuid.uuid4()),
        )
        self.name = data.get("name", valtype=str)
        self.raw_data = data

    def _parse_steps(self, steps: list[AutoFormatDict]) -> None:
        """Parse the steps.

        Args:
            steps (list[AutoFormatDict]): The steps dict data.

        Returns:
            Step: The first step.
        """

        first_step = None
        prev_step = None

        step_ids = []

        for step_data in steps:
            if not isinstance(step_data, dict):
                raise RUValueException(_("A workflow step must be a dict."))
            step_id = step_data.get(
                "id",
                valtype=str,
                default=str(uuid.uuid4()),
            )
            step_name = step_data.get("name", valtype=str, default="")
            step_type = step_data.get("type", valtype=str, default="")
            step_cls: type = None

            step_data["id"] = step_id
            if step_id in step_ids:
                raise RUValueException(
                    format_str(
                        _("Step id '${{step_id}}' is duplicated."),
                        fmt={"step_id": make_pretty(step_id)},
                    )
                )
            step_ids.append(step_id)

            if not step_type:
                for cls, contribute in step_contribute.items():
                    is_match = all(
                        step_data.get(contribute_item, None) is not None
                        for contribute_item in contribute  # All items exist.
                    )
                    if is_match:
                        step_cls = cls
                        break
            else:
                step_cls = step_types.get(step_type, None)
                if step_cls is None:
                    raise RUValueException(
                        format_str(
                            _(
                                "Unknown step type: '${{step_type}}' of step "
                                "'${{step_name}}'. Please check the workflow."
                            ),
                            fmt={
                                "step_type": make_pretty(step_type),
                                "step_name": make_pretty(step_name),
                            },
                        ),
                        hint=_(
                            "Please check typo or use 'type' attribute manually.",  # noqa: E501
                        ),
                    )

            if step_cls is None:
                raise RUValueException(
                    format_str(
                        _(
                            "The type of step '${{step}}'[black](${{step_id}})"
                            "[/black] in workflow '${{workflow}}'[black]("
                            "${{workflow_id}})[/black] is not provided and "
                            "could not be inferred.",
                        ),
                        fmt={
                            "step": make_pretty(step_name, _("<Unnamed>")),
                            "workflow": make_pretty(self.name, _("<Unnamed>")),
                            "step_id": step_id,
                            "workflow_id": self.id,
                        },
                    )
                )
            step = step_cls(step_data, self)
            call_ktrigger(
                IKernelTrigger.post_run_workflow_step,
                step=step,
            )

            if prev_step is not None:
                prev_step.next = step

            if first_step is None:
                first_step = step

            prev_step = step

        return first_step

    def __str__(self):
        """Return the name of the workflow.

        Returns:
            str: The name of the workflow.
        """
        return self.name

    def __repr__(self):
        """Return the representation of the workflow.

        Returns:
            str: The repr of the workflow.
        """
        return f"<{self.__class__.__name__} {self.name}>"

    def __iter__(self):
        """Iterate over the steps.

        Yields:
            Step: One step.
        """

        cur_step = self.first_step
        while cur_step is not None:
            yield cur_step
            cur_step = cur_step.next

    def run(self):
        """Run the workflow."""

        call_ktrigger(
            IKernelTrigger.pre_run_workflow,
            workflow=self,
        )
        self.first_step = self._parse_steps(
            self.raw_data.get("steps", valtype=list),
        )
        call_ktrigger(
            IKernelTrigger.post_run_workflow,
            workflow=self,
        )


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
            message=format_str(
                _(
                    "Step type '${{name}}' registered multiple times. It's unsafe.",  # noqa: E501
                ),
                fmt={"name": make_pretty(name)},
            ),
        )
    step_types[name] = cls
    if cls not in step_contribute:
        step_contribute[cls] = contributes
    logger.info(
        "Step type %s registered with contributes %s",
        name,
        contributes,
    )


def run_inline_workflow(
    data: AutoFormatDict | list[AutoFormatDict], fail_fast: bool = True
) -> Exception | None:
    """Run a inline workflow

    Args:
        data (AutoFormatDict | list[AutoFormatDict]): Workflow data.
        fail_fast (bool, optional): Raise an exception if run failed.
            Defaults to True.

    Returns:
        Exception | None: If running failed without fail-fast, return its
            exception. Return None if succeed.
    """

    if isinstance(data, list):
        data = AutoFormatDict.from_dict({
            "name": _("<Inline Workflow>"),
            "steps": data,
        })

    wf = Workflow(data)
    try:
        wf.run()
    except Exception as exc:  # pylint: disable=broad-exception-caught
        if fail_fast:
            raise exc from None
        call_ktrigger(
            IKernelTrigger.on_warning,
            message=format_str(
                _(
                    "Workflow running failed: ${{exc}}",
                ),
                fmt={"exc": f"{type(exc).__name__}: {str(exc)}"},
            ),
        )
        return exc
    return None


def run_workflow(file: Path, fail_fast: bool = True) -> Exception | None:
    """Run a workflow file.

    Args:
        file (Path): Workflow file path. It can be a JSON, or a yaml.
        fail_fast (bool, optional): Raise an exception if run failed.

    Raises:
        RUValueException: If workflow's step parse failed.

    Returns:
        Exception | None: If running failed without fail-fast, return its
            exception. Return None if succeed.
    """

    with open(file, encoding=DEFAULT_CHARSET) as f:
        if file.suffix.lower() in [".json", ".json5"]:
            workflow = json.load(f)
        elif file.suffix.lower() in [".yaml", ".yml"]:
            workflow = yaml.safe_load(f)
        else:
            raise RUValueException(
                format_str(
                    _(
                        "The suffix of '[underline]${{path}}[/underline]' "
                        "is invalid."
                    ),
                    fmt={"path": make_pretty(file.absolute())},
                ),
                hint=_("We only support '.json', '.json5', '.yaml', '.yml'."),
            )

        return run_inline_workflow(
            AutoFormatDict.from_dict(workflow),
            fail_fast,
        )


if __name__ == "__main__":
    import rich

    rich.print(f"{__file__}: {__doc__.strip()}")

    run_workflow("workflow.yaml")
