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

"""Stack implementation."""

from queue import Empty, LifoQueue
from time import time
from typing import Any

__all__ = ["Stack"]


class Stack[T](LifoQueue[T]):
    """A LifoQueue that can get the top value."""

    def top(
        self,
        *,
        block: bool = True,
        timeout: int | None = None,
    ) -> Any:  # noqa: ANN401
        """Get the top value of the stack.

        Args:
            block (bool): If it is True, block until an item is available.
            timeout (int | None): If it is positive, block at most timeout
                seconds.

        Returns:
            Any: The top value of the stack.

        """
        with self.not_empty:
            if not block:
                if not self._qsize():
                    raise Empty
            elif timeout is None:
                while not self._qsize():
                    self.not_empty.wait()
            elif timeout < 0:
                msg = "'timeout' must be a non-negative number"
                raise ValueError(msg)
            else:
                endtime = time() + timeout
                while not self._qsize():
                    remaining = endtime - time()
                    if remaining <= 0.0:
                        raise Empty
                    self.not_empty.wait(remaining)
            return self.queue[-1]

    def top_nowait(self) -> Any:  # noqa: ANN401
        """Get the top value of the stack without blocking.

        Returns:
            Any: The top value of the stack.

        """
        return self.top(block=False)

    def __str__(self) -> str:
        """Get the string representation of the stack.

        Returns:
            The string representation of the stack.

        """
        return self.__repr__()

    def __repr__(self) -> str:
        """Get the string representation of the stack.

        Returns:
            The string representation of the stack.

        """
        return f"[{', '.join([repr(item) for item in self.queue])}>"
