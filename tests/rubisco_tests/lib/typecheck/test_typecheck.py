# -*- mode: python -*-
# vi: set ft=python :

# Copyright (C) 2025 The C++ Plus Project.
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

"""Test rubisco.lib.typecheck.typecheck module."""

from types import EllipsisType, NoneType
from typing import Any

import pytest

from rubisco.lib.typecheck import is_instance


class TestIsInstance:
    """Test is_instance."""

    def test_single_type(self) -> None:
        """Test single type."""
        if not is_instance(1, int) or not is_instance("test", str):
            pytest.fail("Type check failed.")
        if not is_instance(obj=True, objtype=bool):
            pytest.fail("Type check failed.")
        if not is_instance(None, NoneType) or not is_instance(None, None):
            pytest.fail("Type check failed.")
        if not is_instance(..., EllipsisType):
            pytest.fail("Type check failed.")
        if (
            not is_instance({}, dict)
            or not is_instance([], list)
            or not is_instance((), tuple)
            or not is_instance(set(), set)
        ):
            pytest.fail("Type check failed.")

    def test_union_type(self) -> None:
        """Test union type."""
        if not is_instance(1, int | str):
            pytest.fail("Type check failed.")
        if not is_instance("test", int | str):
            pytest.fail("Type check failed.")
        if not is_instance(None, NoneType | None):
            pytest.fail("Type check failed.")
        if not is_instance(..., EllipsisType | None):
            pytest.fail("Type check failed.")
        if not is_instance(1, int | str) or not is_instance("", int | str):
            pytest.fail("Type check failed.")
        if is_instance([], int | str):
            pytest.fail("Type check failed.")

    def test_generic_alias(self) -> None:
        """Test generic alias."""
        if not is_instance([1, 2, 3], list[int]):
            pytest.fail("Type check failed.")
        if is_instance((1, 2, 3), list[int]):
            pytest.fail("Type check failed.")
        if is_instance([1, 2, 3], list[str]):
            pytest.fail("Type check failed.")
        if not is_instance([1, 2, 3], list[int | str]):
            pytest.fail("Type check failed.")
        if not is_instance([1, "", "", None, 1, 5], list[int | str | None]):
            pytest.fail("Type check failed.")
        if not is_instance((1, 2, 3), tuple[int]) or not is_instance(
            (1, 2, 3),
            tuple[int, ...],
        ):
            pytest.fail("Type check failed.")
        if (
            not is_instance((1, 2, 3), tuple[int | str])
            or not is_instance((1, 2, 3), tuple)
            or not is_instance((1, 2, 3), tuple[int, int, int])
            or not is_instance((1, 2, 3), tuple[int])
            or is_instance((1, 2, 3), tuple[int, str, str | int])
        ):
            pytest.fail("Type check failed.")

    def test_generic_alias_dict(self) -> None:
        """Test generic alias dict."""
        if not is_instance({}, dict[str, str]):
            pytest.fail("Type check failed.")
        if not is_instance({"a": "b"}, dict[str, str]):
            pytest.fail("Type check failed.")
        if not is_instance({"a": 1}, dict[str, int]):
            pytest.fail("Type check failed.")
        if not is_instance({"a": 1}, dict[str, int | str]):
            pytest.fail("Type check failed.")
        if not is_instance({"a": 1, "b": "c"}, dict[str, int | str]):
            pytest.fail("Type check failed.")
        if not is_instance({"a": 1, "b": None}, dict[str, int | None]):
            pytest.fail("Type check failed.")

    def test_nested(self) -> None:
        """Test nested."""
        if not is_instance(
            {"a": {"b": 1}},
            dict[str, dict[str, int]],
        ):
            pytest.fail("Type check failed.")
        if is_instance(
            {"a": {"b": 1}},
            dict[str, dict[str, str]],
        ):
            pytest.fail("Type check failed.")
        if not is_instance(
            {"a": {"b": [(1, 2, 3), None]}, "c": 1},
            dict[str, dict[str, list[tuple[int, ...] | None]] | int],
        ):
            pytest.fail("Type check failed.")
        if is_instance(
            {"a": {"b": [(1, 2, 3), None]}, "c": 1},
            dict[str, dict[str, list[tuple[int, str] | None]] | int],
        ):
            pytest.fail("Type check failed.")

    def test_any(self) -> None:
        """Test objtype is object."""
        if not is_instance(1, object):
            pytest.fail("Type check failed.")
        if not is_instance("test", object):
            pytest.fail("Type check failed.")
        if not is_instance(None, object):
            pytest.fail("Type check failed.")
        if not is_instance(..., object):
            pytest.fail("Type check failed.")
        if not is_instance(Any, object):
            pytest.fail("Type check failed.")

    def test_unmatched(self) -> None:
        """Test unmatched types."""
        if is_instance(1, list):
            pytest.fail("Type check failed.")
        if is_instance("test", list[None]):
            pytest.fail("Type check failed.")
        if is_instance(None, list[int | str]):
            pytest.fail("Type check failed.")
        if not is_instance([1, 2, 3], list[int | str]):
            pytest.fail("Type check failed.")
        if is_instance(
            {
                "a": {"b": [(1, 2, 3), None]},
                "c": 1,
            },
            dict[str, int],
        ):
            pytest.fail("Type check failed.")
