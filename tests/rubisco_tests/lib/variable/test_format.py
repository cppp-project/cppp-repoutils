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

"""Test rubisco.lib.variable.format module."""

from typing import TYPE_CHECKING

import pytest

from rubisco.lib.exceptions import RUExprError, RUTypeError
from rubisco.lib.variable.format import (
    FormatMode,
    format_dict,
    format_list,
    format_str,
)
from rubisco.lib.variable.variable import push_variables, variables

if TYPE_CHECKING:
    from types import FunctionType


class TestFormatStr:
    """Test format_str."""

    def _reset(self) -> None:
        variables.clear()

    def test_empty(self) -> None:
        """Test empty string."""
        self._reset()
        if format_str("") != "":
            pytest.fail("format_str() should return empty string")

    def test_no_var(self) -> None:
        """Test no variable."""
        self._reset()
        if format_str("hello") != "hello":
            pytest.fail("format_str() should return the same string")

    def test_var(self) -> None:
        """Test variable."""
        self._reset()
        if format_str("hello ${{var}}", fmt={"var": "world"}) != "hello world":
            pytest.fail("format_str() should return the formatted string")

    def test_var_with_decoration(self) -> None:
        """Test variable with decoration."""
        self._reset()
        if format_str("hello ${{var:1}}") != "hello 1":
            pytest.fail("format_str() should return the formatted string")

    def test_var_with_pyexpr(self) -> None:
        """Test variable with python expression."""
        self._reset()
        if (
            format_str(
                "hello ${{var:$&{{1+1}}}}}}",
                mode=FormatMode.NONE | FormatMode.EXECUTE,
            )
            != "hello 2}}"
        ):
            pytest.fail("format_str() should return the formatted string")


class TestFormatList:
    """Test format_list."""

    def _reset(self) -> None:
        variables.clear()

    def test_format_list(self) -> None:
        """Test format_list function."""
        self._reset()

        items: list[str | int | list[str]] = [
            "hello ${{global}}",
            42,
            ["nested ${{func}}"],
            " ${{global2}}",
        ]
        push_variables("global", 111)
        push_variables("global2", "world")
        fmt = {"global": "world", "func": "text"}
        formatted = list(format_list(items, fmt=fmt))
        ans: list[str | int | list[str]] = [
            "hello world",
            42,
            ["nested text"],
            " world",
        ]
        if formatted != ans:
            pytest.fail(f"format_list() should return {ans}, got {formatted}")

    def test_not_str_format_list(self) -> None:
        """Test format_list with non-str items."""
        self._reset()

        items: list[str | dict[str, str]] = [
            "Str",
            "${{intvar}}",
            {
                "X": "X ${{intvar}}",
            },
        ]
        fmt = {"intvar": 100}
        formatted = list(format_list(items, fmt=fmt))
        ans: list[str | int | dict[str, str]] = [
            "Str",
            100,
            {
                "X": "X 100",
            },
        ]
        if formatted != ans:
            pytest.fail(f"format_list() should return {ans}, got {formatted}")

    def test_format_list_typecheck(self) -> None:
        """Test format_list type checking."""
        self._reset()

        excobj = Exception()
        items: list[str | int | dict[str, int] | Exception] = [
            "Str",
            {
                "a": 1,
            },
            "A ${{intvar}}",
            excobj,
            "${{iterfunc}}",
            "${{intvar}}",
        ]

        res = format_list(
            items,
            fmt={
                "intvar": 200,
                "iterfunc": iter,
            },
        )
        ans: list[str | int | dict[str, int] | FunctionType | Exception] = [
            "Str",
            {
                "a": 1,
            },
            "A 200",
            excobj,
            iter,
            200,
        ]
        if res != ans:
            pytest.fail(f"format_list() should return {ans}, got {res}")

    def test_format_list_typecheck_error(self) -> None:
        """Test format_list type checking error."""
        self._reset()

        items: list[str | int] = [
            "Str",
            "${{intvar}}",
            "A ${{intvar}}",
        ]

        with pytest.raises(RUExprError):
            format_list(items)

        with pytest.raises(RUTypeError):
            format_list(items, fmt={"intvar": 200}, valtype=list[str])

    def test_format_list_pyexpr(self) -> None:
        """Test format_list with python expression."""
        self._reset()

        items: list[str] = [
            "Value: $&{{1 + 2}}",
            "Value: $&{{'a' * 3}}",
            "$&{{ None }}",
        ]

        res = format_list(
            items,
            mode=FormatMode.NONE | FormatMode.EXECUTE,
            valtype=list[str | None],
        )
        ans: list[str | None] = [
            "Value: 3",
            "Value: aaa",
            None,
        ]
        if res != ans:
            pytest.fail(f"format_list() should return {ans}, got {res}")

        with pytest.raises(RUExprError):
            format_list(
                ["Value: $&{{1 / 0}}"],
                mode=FormatMode.NONE | FormatMode.EXECUTE,
            )

        with pytest.raises(RUTypeError):
            format_list(
                ["$&{{1 / 2}}"],
                mode=FormatMode.NONE | FormatMode.EXECUTE,
                valtype=list[str],
            )


class TestFormatDict:
    """Test format_dict."""

    def _reset(self) -> None:
        variables.clear()

    def test_format_dict(self) -> None:
        """Test format_dict function."""
        self._reset()

        dct: dict[str, str | int | list[str]] = {
            "greet": "hello ${{global}}",
            "answer": 42,
            "nested": ["nested ${{func}}"],
            "space": " ${{global2}}",
        }
        push_variables("global", 111)
        push_variables("global2", "world")
        fmt = {"global": "world", "func": "text"}
        formatted = format_dict(dct, fmt=fmt)
        ans: dict[str, str | int | list[str]] = {
            "greet": "hello world",
            "answer": 42,
            "nested": ["nested text"],
            "space": " world",
        }
        if formatted != ans:
            pytest.fail(f"format_dict() should return {ans}, got {formatted}")

    def test_format_dict_typecheck(self) -> None:
        """Test format_dict type checking."""
        self._reset()

        dct: dict[str, str | int | dict[str, int]] = {
            "Str": "Str",
            "NumDict": {
                "a": 1,
            },
            "Greeting": "A ${{intvar}}",
            "Number": "${{intvar}}",
        }

        res = format_dict(
            dct,
            fmt={
                "intvar": 200,
            },
        )
        ans: dict[str, str | int | dict[str, int]] = {
            "Str": "Str",
            "NumDict": {
                "a": 1,
            },
            "Greeting": "A 200",
            "Number": 200,
        }
        if res != ans:
            pytest.fail(f"format_dict() should return {ans}, got {res}")

    def test_format_dict_typecheck_error(self) -> None:
        """Test format_dict type checking error."""
        self._reset()

        dct: dict[str, str | int] = {
            "Str": "Str",
            "Num": "${{intvar}}",
            "Greeting": "A ${{intvar}}",
        }

        with pytest.raises(RUExprError):
            format_dict(dct)

        with pytest.raises(RUTypeError):
            format_dict(dct, fmt={"intvar": 200}, valtype=dict[str, int])

        format_dict(dct, fmt={"intvar": 200}, valtype=dict[str, int | str])

    def test_format_dict_pyexpr(self) -> None:
        """Test format_dict with python expression."""
        self._reset()

        dct: dict[str, str] = {
            "Value1": "Value: $&{{1 + 2}}",
            "Value2": "Value: $&{{'a' * 3}}",
            "Value3": "$&{{ None }}",
        }
        res = format_dict(
            dct,
            mode=FormatMode.NONE | FormatMode.EXECUTE,
            valtype=dict[str, str | None],
        )
        ans: dict[str, str | None] = {
            "Value1": "Value: 3",
            "Value2": "Value: aaa",
            "Value3": None,
        }
        if res != ans:
            pytest.fail(f"format_dict() should return {ans}, got {res}")

        with pytest.raises(RUExprError):
            format_dict(
                {"Value1": "Value: $&{{1 / 0}}"},
                mode=FormatMode.NONE | FormatMode.EXECUTE,
            )

        with pytest.raises(RUTypeError):
            format_dict(
                {"Value1": "$&{{1 / 2}}"},
                mode=FormatMode.NONE | FormatMode.EXECUTE,
                valtype=dict[str, str],
            )
