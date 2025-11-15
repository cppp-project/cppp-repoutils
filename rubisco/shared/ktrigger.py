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

"""Rubisco kernel trigger.

Kernel trigger is called when kernel do something. It makes User Control
Interface can do something before or after kernel operations.
"""

from __future__ import annotations

from collections.abc import Callable
from enum import Enum
from functools import partial
from typing import TYPE_CHECKING, Any

from rubisco.lib.exceptions import RUValueError
from rubisco.lib.l10n import _
from rubisco.lib.log import logger
from rubisco.lib.variable.fast_format_str import fast_format_str

if TYPE_CHECKING:
    from pathlib import Path

    from rubisco.envutils.env import RUEnvironment
    from rubisco.envutils.packages import ExtensionPackageInfo
    from rubisco.kernel.project_config.project_config import ProjectConfigration
    from rubisco.kernel.workflow.step import Step, Workflow
    from rubisco.lib.process import Process
    from rubisco.lib.version import Version
    from rubisco.shared.extension import IRUExtension

__all__ = [
    "IKernelTrigger",
    "OutputMethod",
    "bind_ktrigger_interface",
    "call_ktrigger",
]


def _null_trigger(
    name: str,
    *args: Any,  # noqa: ANN401
    **kwargs: Any,  # noqa: ANN401
) -> None:
    logger.debug(
        "Not implemented KTrigger '%s' called(%s, %s).",
        name,
        repr(args),
        repr(kwargs),
    )


class OutputMethod(Enum):
    """Output method.

    Note that RUTree will be always formatted, but it's item will follow this
    setting.
    """

    # Output raw message.
    # Output message as-is. If the message is a str, it will be output as-is.
    # Otherwise, it will be output by repr().
    RAW = 0

    # Format message by type.
    # If the message is a str, it will be output as-is.
    # Otherwise, it will be output by its type. For example, if the message is
    # a serializable object, it will be output as a JSON string.
    FORMAT_TYPE = 1

    # Format message by Rich markup.
    # It will be formatted by Rich markup.
    FORMAT_MARKUP = 2

    # Format message in Markdown format.
    FORMAT_MARKDOWN = 3


class IKernelTrigger:  # pylint: disable=too-many-public-methods
    """Kernel trigger interface."""

    def pre_exec_process(self, *, proc: Process) -> None:
        """Pre-exec process.

        Args:
            proc (Process): Process instance.

        """
        _null_trigger("pre_exec_process", proc=proc)

    def post_exec_process(
        self,
        *,
        proc: Process,
        retcode: int,
        raise_exc: bool,
    ) -> None:
        """Post-exec process.

        Args:
            proc (Process): Process instance.
            retcode (int): Return code.
            raise_exc (bool): If raise exception.

        """
        _null_trigger(
            "post_exec_process",
            proc=proc,
            retcode=retcode,
            raise_exc=raise_exc,
        )

    def file_exists(self, *, path: Path) -> None:
        """Ask user to overwrite a file.

        Args:
            path (Path): File path.

        """
        _null_trigger("file_exists", path=path)

    def on_new_task(
        self,
        *,
        task_start_msg: str,
        task_name: str,
        total: float,
    ) -> None:
        """When a progressive task is created.

        Args:
            task_start_msg (str): Task start message.
            task_name (str): Task name.
            total (float): Total steps. -1 means infinite.

        """
        _null_trigger(
            "on_new_task",
            task_start_msg=task_start_msg,
            task_name=task_name,
            total=total,
        )

    def on_progress(  # pylint: disable=R0913
        self,
        *,
        task_name: str,
        current: float,
        delta: bool = False,
        update_msg: str = "",
        status_msg: str = "",
    ) -> None:
        """When the progressive task progress is updated.

        Args:
            task_name (str): Task name. It's the unique identifier of the
                task.
            current (int | float): Current step.
            delta (bool): If the current is delta.
            update_msg (str): Update message.
            status_msg (str): Status message.

        """
        _null_trigger(
            "on_progress",
            task_name=task_name,
            current=current,
            delta=delta,
            update_msg=update_msg,
            status_msg=status_msg,
        )

    def set_progress_total(self, *, task_name: str, total: float) -> None:
        """Set the total steps of a progressive task.

        Args:
            task_name (str): Task name.
            total (float): Total steps.

        """
        _null_trigger(
            "set_progress_total",
            task_name=task_name,
            total=total,
        )

    def on_finish_task(self, *, task_name: str) -> None:
        """When a progressive task is finished.

        Args:
            task_name (str): Task name.

        """
        _null_trigger("on_finish_task", task_name=task_name)

    def on_syspkg_installation_skip(
        self,
        *,
        packages: list[str],
        message: str,
    ) -> None:
        """When a system package installation is skipped.

        Args:
            packages (list[str]): Package name.
            message (str): Skip reason.

        """
        _null_trigger(
            "on_syspkg_installation_skip",
            packages=packages,
            message=message,
        )

    def on_update_git_repo(self, *, path: Path, branch: str) -> None:
        """When a git repository is updating.

        Args:
            path (Path): Repository path.
            branch (str): Branch name.

        """
        _null_trigger(
            "on_update_git_repo",
            path=path,
            branch=branch,
        )

    def on_clone_git_repo(
        self,
        *,
        url: str,
        path: Path,
        branch: str,
    ) -> None:
        """When a git repository is cloning.

        Args:
            url (str): Repository URL.
            path (Path): Repository path.
            branch (str): Branch name.

        """
        _null_trigger(
            "on_clone_git_repo",
            url=url,
            path=path,
            branch=branch,
        )

    def on_hint(self, *, message: str) -> None:
        """When a hint is got.

        Args:
            message (str): Hint message.

        """
        _null_trigger("on_hint", message=message)

    def on_warning(self, *, message: str) -> None:
        """When a warning is raised.

        Args:
            message (str): Warning message.

        """
        _null_trigger("on_warning", message=message)

    def on_error(self, *, message: str) -> None:
        """When a error is raised.

        Args:
            message (str): Error message.

        """
        _null_trigger("on_error", message=message)

    def pre_speedtest(self, *, host: str) -> None:
        """When a speed test task is started.

        Args:
            host (str): Host to test.

        """
        _null_trigger("pre_speedtest", host=host)

    def post_speedtest(self, *, host: str, speed: int) -> None:
        """When a speed test task is finished.

        Args:
            host (str): Host to test.
            speed (int): Speed of the host. (us)
                `-1` means canceled, `C_INTMAX` means failed.

        """
        _null_trigger("post_speedtest", host=host, speed=speed)

    def stop_speedtest(self, *, choise: str | None) -> None:
        """When a speed test task is stopped.

        Args:
            choise (str | None): User's choise. None means error.

        """
        _null_trigger("stop_speedtest", choise=choise)

    def pre_run_workflow_step(self, *, step: Step) -> None:
        """When a workflow is started.

        Args:
            step (Step): The step.

        """
        _null_trigger("pre_run_workflow_step", step=step)

    def post_run_workflow_step(self, *, step: Step) -> None:
        """When a workflow is finished.

        Args:
            step (Step): The step.

        """
        _null_trigger("post_run_workflow_step", step=step)

    def pre_run_workflow(self, *, workflow: Workflow) -> None:
        """When a workflow is started.

        Args:
            workflow (Workflow): The workflow.

        """
        _null_trigger("pre_run_workflow", workflow=workflow)

    def post_run_workflow(self, *, workflow: Workflow) -> None:
        """When a workflow is finished.

        Args:
            workflow (Workflow): The workflow.

        """
        _null_trigger("post_run_workflow", workflow=workflow)

    def pre_run_matrix(self, *, variables: dict[str, object]) -> None:
        """When a matrix job is started.

        Args:
            variables (dict[str, object]): The variables.

        """
        _null_trigger("pre_run_matrix", variables=variables)

    def post_run_matrix(self, *, variables: dict[str, object]) -> None:
        """When a matrix job is finished.

        Args:
            variables (dict[str, object]): The variables.

        """
        _null_trigger("post_run_matrix", variables=variables)

    def on_mkdir(self, *, path: Path) -> None:
        """On we are creating directories.

        Args:
            path (Path): Directory/directories's path.

        """
        _null_trigger("on_mkdir", path=path)

    def on_file_selected(self, *, path: Path) -> None:
        """On a file selected.

        Args:
            path (Path): File path.

        """
        _null_trigger("on_file_selected", path=path)

    def on_output(
        self,
        *,
        message: object,
        method: OutputMethod = OutputMethod.FORMAT_MARKUP,
    ) -> None:
        """Output a message.

        Args:
            message (object): Message or object to output.
            method (OutputMethod, optional): Output method. Defaults to
                OutputMethod.FORMAT_MARKUP.

        """
        _null_trigger("on_output", message=message, method=method)

    def on_move_file(self, *, src: Path, dst: Path) -> None:
        """On we are moving files.

        Args:
            src (Path): Source file path.
            dst (Path): Destination file path.

        """
        _null_trigger("on_move_file", src=src, dst=dst)

    def on_copy(self, *, src: Path, dst: Path) -> None:
        """On we are copying files.

        Args:
            src (Path): Source file path.
            dst (Path): Destination file path.

        """
        _null_trigger("on_copy", src=src, dst=dst)

    def on_remove(self, *, path: Path) -> None:
        """On we are removing files.

        Args:
            path (Path): File path.

        """
        _null_trigger("on_remove", path=path)

    def on_extension_loaded(
        self,
        *,
        instance: IRUExtension,
        ext_info: ExtensionPackageInfo,
    ) -> None:
        """On a extension loaded.

        Args:
            instance (IRUExtension): Extension instance.
            ext_info (ExtensionPackageInfo): Extension information.

        """
        _null_trigger(
            "on_extension_loaded",
            instance=instance,
            ext_info=ext_info,
        )

    def on_show_project_info(self, *, project: ProjectConfigration) -> None:
        """On show project information.

        Args:
            project (ProjectConfigration): Project configuration.

        """
        _null_trigger("on_show_project_info", project=project)

    def on_mklink(
        self,
        *,
        src: Path,
        dst: Path,
        symlink: bool,
    ) -> None:
        """On we are creating a symlink.

        Args:
            src (Path): Source file path.
            dst (Path): Destination file path.
            symlink (bool): If it is a symlink.

        """
        _null_trigger("on_mklink", src=src, dst=dst, symlink=symlink)

    def on_create_venv(self, *, path: Path) -> None:
        """On we are creating a virtual environment.

        Args:
            path (Path): Virtual environment path.

        """
        _null_trigger("on_create_venv", path=path)

    def on_install_extension(
        self,
        *,
        dest: RUEnvironment,
        ext_name: str,
        ext_version: Version,
    ) -> None:
        """On we are installing an extension.

        Args:
            dest (RUEnvironment): Destination environment.
            ext_name (str): Extension name.
            ext_version (Version): Extension version.

        """
        _null_trigger(
            "on_install_extension",
            dest=dest,
            ext_name=ext_name,
            ext_version=ext_version,
        )

    def on_extension_installed(
        self,
        *,
        dest: RUEnvironment,
        ext_name: str,
        ext_version: Version,
    ) -> None:
        """On a extension installed.

        Args:
            dest (RUEnvironment): Destination environment type.
            ext_name (str): Extension name.
            ext_version (Version): Extension version.

        """
        _null_trigger(
            "on_extension_installed",
            dest=dest,
            ext_name=ext_name,
            ext_version=ext_version,
        )

    def on_uninstall_extension(
        self,
        *,
        dest: RUEnvironment,
        ext_name: str,
        ext_version: Version,
    ) -> None:
        """On we are removing an extension.

        Args:
            dest (RUEnvironment): Destination environment type.
            ext_name (str): Extension name.
            ext_version (Version): Extension version.

        """
        _null_trigger(
            "on_uninstall_extension",
            dest=dest,
            ext_name=ext_name,
            ext_version=ext_version,
        )

    def on_extension_uninstalled(
        self,
        *,
        dest: RUEnvironment,
        ext_name: str,
        ext_version: Version,
    ) -> None:
        """On a extension removed.

        Args:
            dest (RUEnvironment): Destination environment type.
            ext_name (str): Extension name.
            ext_version (Version): Extension version.

        """
        _null_trigger(
            "on_extension_uninstalled",
            dest=dest,
            ext_name=ext_name,
            ext_version=ext_version,
        )

    def on_upgrade_extension(
        self,
        *,
        dest: RUEnvironment,
        ext_name: str,
        ext_version: Version,
    ) -> None:
        """On we are upgrading an extension.

        Args:
            dest (RUEnvironment): Destination environment type.
            ext_name (str): Extension name.
            ext_version (Version): Extension version.

        """
        _null_trigger(
            "on_upgrade_extension",
            dest=dest,
            ext_name=ext_name,
            ext_version=ext_version,
        )

    def on_extension_upgraded(
        self,
        *,
        dest: RUEnvironment,
        ext_name: str,
        ext_version: Version,
    ) -> None:
        """On a extension upgraded.

        Args:
            dest (RUEnvironment): Destination environment type.
            ext_name (str): Extension name.
            ext_version (Version): Extension version.

        """
        _null_trigger(
            "on_extension_upgraded",
            dest=dest,
            ext_name=ext_name,
            ext_version=ext_version,
        )

    def on_verify_uninstall_extension(
        self,
        *,
        dest: RUEnvironment,
        query: set[ExtensionPackageInfo],
    ) -> None:
        """On we are verifying an extension.

        Args:
            dest (RUEnvironment): Destination environment type.
            query (set[ExtensionPackageInfo]): The extensions to be
                uninstalled.

        Raises:
            Raise KeyboardInterrupt to cancel the uninstallation.

        """
        _null_trigger(
            "on_verify_uninstall_extension",
            dest=dest,
            query=query,
        )

    def on_wait(
        self,
        *,
        msg: str,
        cur_time: int,
    ) -> None:
        """Update waiting message.

        Args:
            msg (str): Waiting message.
            cur_time (int): Current time.

        Raises:
            RUValueError: Waiting message is empty.

        """
        _null_trigger("on_wait", msg=msg, cur_time=cur_time)

    def end_wait(
        self,
        *,
        msg: str,
    ) -> None:
        """End for waiting.

        Args:
            msg (str): The wait message.

        """
        _null_trigger("end_wait", msg=msg)

    def on_step(
        self,
        *,
        msg: str,
    ) -> None:
        """Update step message.

        Args:
            msg (str): Step message.

        """
        _null_trigger("on_step", msg=msg)

    def on_steptask_start(
        self,
        *,
        msg: str,
    ) -> None:
        """On step task started.

        Args:
            msg (str): Step message.

        """
        _null_trigger("on_steptask_start", msg=msg)

    def on_steptask_end(
        self,
        *,
        msg: str,
    ) -> None:
        """On step task ended.

        Args:
            msg (str): Step message.

        """
        _null_trigger("on_steptask_end", msg=msg)

    def on_chdir(
        self,
        *,
        path: Path,
    ) -> None:
        """On change working directory.

        Args:
            path (Path): New working directory.

        """
        _null_trigger("on_chdir", path=path)

    def on_leaving_dir(
        self,
        *,
        path: Path,
    ) -> None:
        """On leaving working directory.

        Args:
            path (Path): New working directory.

        """
        _null_trigger("on_leaving_dir", path=path)


# KTrigger instances.
ktriggers: dict[str, IKernelTrigger] = {}


def bind_ktrigger_interface(kid: str, instance: IKernelTrigger) -> None:
    """Bind a KTrigger instance with a id.

    Args:
        kid (str): KTrigger's id. It MUST be unique.
        instance (IKernelTrigger): KTrigger instance.

    Raises:
        RUValueError: If id is already exists.
        TypeError: If instance is not a IKernelTrigger instance.

    """
    if kid in ktriggers:
        raise RUValueError(
            fast_format_str(
                _("Kernel trigger id '${{name}}' is already exists."),
                fmt={"name": kid},
            ),
        )

    ktriggers[kid] = instance
    logger.debug("Bind kernel trigger '%s' to '%s'.", kid, repr(instance))


def call_ktrigger(
    name: str | Callable[..., None],
    **kwargs: Any,  # noqa: ANN401
) -> None:
    """Call a KTrigger.

    Args:
        name (str | Callable): KTrigger's name.
        **kwargs (Any): Keyword arguments

    Hint:
        Passing arguments by kwargs is recommended. It can make the code
        more readable and avoid bug caused by the wrong order of arguments.

    """
    if isinstance(name, Callable):
        name = name.__name__
    logger.debug(
        "Calling kernel trigger '%s'(%s). %s",
        name,
        repr(kwargs),
        repr(list(ktriggers.keys())),
    )
    for instance in ktriggers.values():
        getattr(instance, name, partial(_null_trigger, name))(**kwargs)


# Death is a form of liberation.
