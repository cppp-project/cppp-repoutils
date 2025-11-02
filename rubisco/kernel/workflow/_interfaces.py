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

"""Interfaces for workflow module.

To avoid circular import, we use the protocol to define the interface.
"""

from pathlib import Path
from typing import ClassVar, Protocol, runtime_checkable

from rubisco.envutils.env import RUEnvironment
from rubisco.envutils.packages import ExtensionPackageInfo

__all__ = ["WorkflowInterfaces"]


def _notimplemented(*args: object, **kwargs: object) -> None:
    raise NotImplementedError


class WorkflowInterfaces:
    """Interfaces for workflow module."""

    @runtime_checkable
    class _LoadExtensionFunction(Protocol):  # pylint: disable=R0903
        def __call__(
            self,
            ext: Path | str | ExtensionPackageInfo,
            env: RUEnvironment,
            *,
            strict: bool = False,
        ) -> None: ...

    _load_extension: ClassVar[_LoadExtensionFunction] = _notimplemented

    @classmethod
    def get_load_extension(cls) -> _LoadExtensionFunction:
        """Get the extension loader. For internal use only.

        Returns:
            _LoadExtensionFunction: The extension loader.

        """
        return cls._load_extension

    @classmethod
    def set_load_extension(cls, extloader: _LoadExtensionFunction) -> None:
        """Set the extension loader. For internal use only.

        Args:
            extloader (_LoadExtensionFunction): The extension loader.

        """
        cls._load_extension = extloader

    @runtime_checkable
    class _RunWorkflowFunction(Protocol):  # pylint: disable=R0903
        def __call__(
            self,
            file: Path,
            *,
            fail_fast: bool = True,
            chdir: Path | None = None,
        ) -> BaseException | None: ...

    _run_workflow: ClassVar[_RunWorkflowFunction] = _notimplemented

    @classmethod
    def get_run_workflow(cls) -> _RunWorkflowFunction:
        """Get the workflow runner. For internal use only.

        Returns:
            _RunWorkflowFunction: The workflow runner.

        """
        return cls._run_workflow

    @classmethod
    def set_run_workflow(cls, runner: _RunWorkflowFunction) -> None:
        """Set the workflow runner. For internal use only.

        Args:
            runner (_RunWorkflowFunction): The workflow runner.

        """
        cls._run_workflow = runner

    @runtime_checkable
    class _RunInlineWorkflowFunction(Protocol):  # pylint: disable=R0903
        def __call__(
            self,
            data: dict[str, object] | list[dict[str, object]],
            default_id: str,
            *,
            fail_fast: bool = True,
        ) -> BaseException | None: ...

    _run_inline_workflow: ClassVar[_RunInlineWorkflowFunction] = _notimplemented

    @classmethod
    def get_run_inline_workflow(cls) -> _RunInlineWorkflowFunction:
        """Get the workflow runner. For internal use only.

        Returns:
            _RunWorkflowFunction: The workflow runner.

        """
        return cls._run_inline_workflow

    @classmethod
    def set_run_inline_workflow(
        cls,
        runner: _RunInlineWorkflowFunction,
    ) -> None:
        """Set the workflow runner. For internal use only.

        Args:
            runner (_RunWorkflowFunction): The workflow runner.

        """
        cls._run_inline_workflow = runner
