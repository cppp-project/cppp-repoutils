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

"""Rubisco UCI APIs.

UCI is User Control Interface. UCI and kernel communicate by Kernel Trigger.
Although you can call ktrigger directly, but we recommend you to use UCI APIs.

Some complex API in Kernel Trigger will be wrapped by this module. But not all
of them.
"""

import types
from typing import Self

from rubisco.lib.tree import Tree
from rubisco.shared.ktrigger import IKernelTrigger, call_ktrigger

__all__ = ["ProgressTask", "TaskStep", "Tree"]


class TaskStep:
    """Task step."""

    msg: str

    def __init__(self, msg: str) -> None:
        """Init task step.

        Args:
            msg (str): Step message.

        """
        self.msg = msg

    def __enter__(self) -> None:
        """Enter task step."""
        call_ktrigger(IKernelTrigger.on_steptask_start, msg=self.msg)

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> None:
        """Exit task step."""
        call_ktrigger(IKernelTrigger.on_steptask_end, msg=self.msg)


class ProgressTask:
    """Progress task."""

    msg: str
    title: str
    total: float
    current: float

    def __init__(self, title: str, msg: str, total: float) -> None:
        """Init progress task.

        Args:
            title (str): Progress title.
            msg (str): Step message for progress task.
            total (float): Total progress.

        """
        self.msg = msg
        self.title = title
        self.total = float(total)
        self.current = 0.0

    def __enter__(self) -> Self:
        """Enter progress task."""
        call_ktrigger(
            IKernelTrigger.on_new_task,
            task_start_msg=self.msg,
            task_name=self.title,
            total=self.total,
        )
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> None:
        """Exit progress task."""
        call_ktrigger(IKernelTrigger.on_finish_task, task_name=self.title)

    def update(
        self,
        current: float,
        *,
        is_advance: bool = False,
        update_msg: str = "",
        status_msg: str = "",
    ) -> None:
        """Update progress task.

        Args:
            current (float): Current progress.
            is_advance (bool, optional): Whether the progress is advanced.
                Defaults to False.
            update_msg (str, optional): Update message. Defaults to "".
            status_msg (str, optional): Status message. Defaults to "".

        """
        if is_advance:
            self.current += current
        call_ktrigger(
            IKernelTrigger.on_progress,
            task_name=self.title,
            current=self.current,
            delta=False,
            update_msg=update_msg,
            status_msg=status_msg,
        )

    def set_total(self, total: float) -> None:
        """Set total progress.

        Args:
            total (float): Total progress.

        """
        self.total = float(total)
        call_ktrigger(
            IKernelTrigger.set_progress_total,
            task_name=self.title,
            total=self.total,
        )
