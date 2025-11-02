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

"""Eval a python expression in a relatively safe container."""

import builtins
import pathlib
import re
from collections.abc import Callable
from types import ModuleType
from typing import Any, NoReturn

from rubisco.lib.exceptions import RUEvalError, RUFunctionDisallowedError
from rubisco.lib.l10n import _
from rubisco.lib.log import logger
from rubisco.lib.variable.variable import get_variable, has_variable, variables

__all__ = ["eval_pyexpr"]


def _copy_builtins() -> object:
    res = ModuleType(_("<rubisco inline python expression>"))
    for name in dir(builtins):
        setattr(res, name, getattr(builtins, name))
    for name, val in variables.items():
        setattr(res, name, val.top())
    return res


def get_disabled_function(name: str) -> Callable[..., NoReturn]:
    """Get a disabled function.

    Args:
        name (str): The name of the function.

    Returns:
        Callable[..., NoReturn]: The disabled function.

    """

    def _disabled(*_args: Any, **_kwargs: Any) -> NoReturn:  # noqa: ANN401
        raise RUFunctionDisallowedError(
            _(
                "${{func}} is disallowed in Rubisco variable expression.",
            ).replace("${{func}}", name),
        )

    return _disabled


def eval_pyexpr(expr: str) -> Any:  # noqa: ANN401
    """Eval a python expression in a relatively safe container.

    Args:
        expr (str): The python expression to eval.

    Returns:
        Any: The result of the python expression.

    Warnings:
        This function is not 100% safe. We trust users because
        Rubisco is a tool for cppp developer(s).

    """
    builtins_ = _copy_builtins()

    # Variables functions.
    builtins_.get_variable = get_variable  # type: ignore[attr-defined]
    builtins_.get = get_variable  # type: ignore[attr-defined]
    builtins_.g = get_variable  # type: ignore[attr-defined]
    builtins_.has_variable = has_variable  # type: ignore[attr-defined]
    builtins_.has = has_variable  # type: ignore[attr-defined]
    builtins_.h = has_variable  # type: ignore[attr-defined]

    # Variables.
    for name, val in variables.items():
        setattr(builtins_, name, val.top())

    # Disable some built-in functions.
    builtins_.__import__ = get_disabled_function("__import__")  # type: ignore[attr-defined]
    builtins_.open = get_disabled_function("open")  # type: ignore[attr-defined]
    builtins_.exec = get_disabled_function("exec")  # type: ignore[attr-defined]
    builtins_.eval = get_disabled_function("eval")  # type: ignore[attr-defined]
    builtins_.compile = get_disabled_function("compile")  # type: ignore[attr-defined]
    builtins_.__spec__ = None  # type: ignore[attr-defined]
    builtins_.__name__ = _("<rubisco inline python expression>")  # type: ignore[attr-defined]
    builtins_.SystemExit = None  # type: ignore[attr-defined]
    builtins_.KeyboardInterrupt = None  # type: ignore[attr-defined]
    builtins_.re = re  # type: ignore[attr-defined]
    builtins_.pathlib = pathlib  # type: ignore[attr-defined]
    builtins_.Path = pathlib.Path  # type: ignore[attr-defined]

    try:
        logger.info("Eval python expression: %s", expr)
        return eval(  # pylint: disable=W0123 # noqa: S307
            expr,
            {"__builtins__": builtins_},
        )
    except RUFunctionDisallowedError:
        raise
    except (Exception, SystemExit, KeyboardInterrupt) as exc:
        raise RUEvalError(
            _("Eval python expression failed: ${{expr}}: ${{exc}}")
            .replace(
                "${{expr}}",
                expr,
            )
            .replace(
                "${{exc}}",
                str(exc),
            ),
            hint=f"{exc.__class__.__name__}: {exc}",
        ) from exc
