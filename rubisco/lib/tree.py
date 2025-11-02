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

"""Rubisco tree wrapper.

Tree is used to represent hierarchical data structures for UCI.
Pass it to `IKernelTrigger.on_output` to output a tree.
"""

__all__ = ["Tree"]


class Tree[T]:
    """Rubisco tree wrapper."""

    value: T
    children: "list[Tree[T]]"
    parent: "Tree[T] | None"

    def __init__(self, value: T, parent: "Tree[T] | None" = None) -> None:
        """Initialize a tree node.

        Args:
            value (T): The value of the node.
            parent (Tree[T] | None, optional): The parent node.
                Defaults to None.

        """
        self.value = value
        self.children = []
        self.parent = parent

    def add(self, child: "Tree[T]") -> None:
        """Add a child to the tree node.

        Args:
            child (Tree[T]): The child node to add.

        """
        self.children.append(child)
        child.parent = self

    def remove(self, child: "Tree[T]") -> None:
        """Remove a child from the tree node.

        Args:
            child (Tree[T]): The child node to remove.

        Raises:
            ValueError: If the child is not found in the children list.

        """
        if child in self.children:
            self.children.remove(child)
            child.parent = None
        else:
            msg = "Child not found in the children list."
            raise ValueError(msg)
