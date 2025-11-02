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

"""MatrixStep implementation."""

import itertools
from collections.abc import Generator
from typing import Any, cast

from rubisco.kernel.workflow._interfaces import WorkflowInterfaces
from rubisco.kernel.workflow.step import Step
from rubisco.lib.typecheck import get_dict_check
from rubisco.lib.variable.format import FormatMode, format_auto
from rubisco.lib.variable.var_container import VariableContainer
from rubisco.shared.ktrigger import IKernelTrigger, call_ktrigger

__all__ = ["MatrixStep"]


def _generate_combinations(
    variables: dict[str, list[Any] | Any],
) -> Generator[dict[str, object]]:
    names = list(variables.keys())
    values = list(variables.values())
    for idx, val in enumerate(values):
        if not isinstance(val, list):
            values[idx] = [val]

    for combination in itertools.product(*values):
        yield format_auto(dict(zip(names, combination, strict=True)))


def allocate_matrix_vars(
    mvars: dict[str, list[Any] | Any] | list[dict[str, Any]],
) -> list[dict[str, object]]:
    """Allocate matrix vars.

    Args:
        mvars (dict[str, list[Any] | Any] | list[dict[str, Any]]): The
            matrix variables. If it is a list, each element must be a dict.
            Otherwise, it is a dict.

    Returns:
        list[dict[str, object]]: The allocated matrix vars. If the input is a
            list , return the same list. Otherwise, return the independent
            assortment of the matrix vars.

    Raises:
        RUTypeError: If the input is not a list[dict[str, Any]] or a
        dict[str, list[Any] | Any].

    """
    if not mvars:
        return []

    if isinstance(mvars, list):
        return [format_auto(v) for v in mvars]

    return list(_generate_combinations(mvars))


def _in(var: dict[str, object], exclude: dict[str, object]) -> bool:
    for key, value in exclude.items():
        if key not in var:
            return False
        if var[key] != value:
            return False
    return True


def exclude_matrix_vars(
    mvars: list[dict[str, object]],
    excludes: dict[str, list[Any] | Any] | list[dict[str, Any]],
) -> list[dict[str, object]]:
    """Exclude matrix vars.

    Args:
        mvars (list[dict[str, object]]): The matrix vars.
        excludes (dict[str, list[Any] | Any] | list[dict[str, Any]]): The
            excludes. If it is a list, each element must be a dict.
            Otherwise, it is a dict.

    Returns:
        list[dict[str, object]]: The excluded matrix vars.

    Raises:
        RUTypeError: If the input is not a list[dict[str, Any]] or a
        dict[str, list[Any] | Any].

    """
    if not excludes:
        return mvars

    excludes_list = allocate_matrix_vars(excludes)

    return [
        format_auto(mvar)
        for mvar in mvars
        if not any(_in(mvar, exclude) for exclude in excludes_list)
    ]


class MatrixStep(Step):
    """Matrix step."""

    matrix_vars: dict[str, list[object] | object] | list[dict[str, object]]
    excludes: dict[str, list[object] | object] | list[dict[str, object]]
    steps: list[dict[str, object]]

    def init(self) -> None:
        """Initialize the step."""
        self.matrix_vars = cast(
            "dict[str, list[object] | object] | list[dict[str, object]]",
            format_auto(
                self.raw_data["matrix"],
                mode=FormatMode.EXECUTE,
                valtype=dict[str, list[object] | object]
                | list[dict[str, object]],
            ),
        )
        self.excludes = cast(
            "dict[str, list[object] | object] | list[dict[str, object]]",
            format_auto(
                self.raw_data.get("excludes", []),
                mode=FormatMode.EXECUTE,
                valtype=dict[str, list[object] | object]
                | list[dict[str, object]],
            ),
        )
        # Steps must be formatted when running. So we save the raw data here.
        self.steps = cast(
            "list[dict[str, object]]",
            get_dict_check(
                self.raw_data,
                "steps",
                valtype=list[dict[str, object]],
            ),
        )

    def _format_steps(self) -> list[dict[str, object]]:
        return format_auto(
            self.steps,
            mode=FormatMode.EXECUTE,
            valtype=list[dict[str, object]],
        )

    def run(self) -> None:
        """Run the step."""
        matrix_vars = allocate_matrix_vars(self.matrix_vars)
        matrix_vars = exclude_matrix_vars(matrix_vars, self.excludes)

        for idx, mvars in enumerate(matrix_vars):
            with VariableContainer(mvars):
                steps = self._format_steps()
                call_ktrigger(IKernelTrigger.pre_run_matrix, variables=mvars)
                default_id = f"{self.id}.matrix.{idx}"
                WorkflowInterfaces.get_run_inline_workflow()(
                    steps,
                    default_id,
                )
                call_ktrigger(IKernelTrigger.post_run_matrix, variables=mvars)
