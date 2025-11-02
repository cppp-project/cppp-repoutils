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

"""Test rubisco.lib.variable.execute module."""

from typing import Any

import pytest

from rubisco.lib.exceptions import (
    RUEvalError,
    RUExprError,
    RUExprPermissionError,
    RUFunctionDisallowedError,
)
from rubisco.lib.variable.execute import execute_expression
from rubisco.lib.variable.lexer import get_token
from rubisco.lib.variable.ru_ast import parse_expression
from rubisco.lib.variable.variable import push_variables


class TestExecuteExpression:
    """Test execute_expression."""

    def _check(self, expr: str, res: str | Any, *, enable_exec: bool) -> None:  # noqa: ANN401
        expr_result = execute_expression(
            parse_expression(get_token(expr)),
            enable_exec=enable_exec,
        )
        if expr_result != res:
            pytest.fail(f"Expression {expr} should be {res}.")

    def test_empty(self) -> None:
        """Test empty expression."""
        self._check("", "", enable_exec=False)

    def test_root(self) -> None:
        """Test root expression."""
        self._check("a", "a", enable_exec=False)

    def test_variable(self) -> None:
        """Test variable expression."""
        push_variables("a", "b")
        self._check("${{a}}", "b", enable_exec=False)
        push_variables("a", 1)
        self._check("${{a}}", 1, enable_exec=False)

    def test_var_decoration(self) -> None:
        """Test variable decoration."""
        self._check("${{_U: c}}", " c", enable_exec=False)
        push_variables("a", "b")
        self._check("${{_U:${{_U:${{a}}}}}}", "b", enable_exec=False)

    def test_pyexpr(self) -> None:
        """Test python expression."""
        self._check("$&{{1+1}}", 2, enable_exec=True)
        push_variables("a", 1)
        self._check("$&{{a+1}}", 2, enable_exec=True)

    def test_pyexpr_get_variable(self) -> None:
        """Test python expression getting variable."""
        push_variables("a", 5)
        self._check("$&{{g('a')}}", 5, enable_exec=True)

    def test_pyexpr_disabled(self) -> None:
        """Test python expression when disabled."""
        pytest.raises(
            RUExprPermissionError,
            self._check,
            "$&{{1+1}}",
            0,
            enable_exec=False,
        )

    def test_pyexpr_disables_nested(self) -> None:
        """Test nested python expression with disabled."""
        pytest.raises(
            RUExprPermissionError,
            self._check,
            "${{x: $&{{3+1}}}}",
            0,
            enable_exec=False,
        )

    def test_pyexpr_disallowed_func(self) -> None:
        """Test python expression with disallowed function."""
        pytest.raises(
            RUFunctionDisallowedError,
            self._check,
            "$&{{open('', 'w')}}",
            0,
            enable_exec=True,
        )

    def test_pyexpr_eval_error(self) -> None:
        """Test python expression with eval error."""
        pytest.raises(
            RUEvalError,
            self._check,
            "$&{{1/0}}",
            0,
            enable_exec=True,
        )

    def test_pyexpr_eval_systemexit(self) -> None:
        """Test python expression with SystemExit."""
        pytest.raises(
            RUEvalError,
            self._check,
            "$&{{exit(1)}}",
            0,
            enable_exec=True,
        )

    def test_nested_all(self) -> None:
        """Test nested all."""
        push_variables("a", None)
        expr = (
            "X${{aa: ${{  Var:$&{{a}}}} Hello}}Y ${{bb: ${{a}}"  # Don't remove.
            "HLWD}}}}s $&{{None}}"
        )
        self._check(expr, "X None HelloY  NoneHLWD}}s None", enable_exec=True)

    def test_undefined_var(self) -> None:
        """Test undefined variable."""
        pytest.raises(
            RUExprError,
            self._check,
            "${{_U}}",
            "",
            enable_exec=False,
        )
