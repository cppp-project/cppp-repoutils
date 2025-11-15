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

"""C++ Plus Rubisco CLI output utils."""

from __future__ import annotations

import json
import os
import random
from typing import TYPE_CHECKING, Any, cast

import json5
import rich
from beartype.roar import BeartypeException
from rich.markdown import Markdown
from rich.markup import escape
from rich.padding import Padding
from rich.text import Text
from rich.tree import Tree

from rubisco.lib.exceptions import RUError
from rubisco.lib.l10n import _
from rubisco.lib.log import logger
from rubisco.lib.typecheck import is_instance
from rubisco.lib.variable.fast_format_str import fast_format_str
from rubisco.shared.api.uci import Tree as RUTree
from rubisco.shared.ktrigger import OutputMethod

if TYPE_CHECKING:
    from rich.console import RenderableType

__all__ = [
    "format_and_output",
    "get_prompt",
    "output_error",
    "output_hint",
    "output_line",
    "output_step",
    "output_warning",
    "pop_level",
    "push_level",
    "show_exception",
    "sum_level_indent",
]

AVAILABLE_STYLES = {
    "b": "blue",
    "g": "green",
    "r": "red",
    "y": "yellow",
    "c": "cyan",
    "m": "magenta",
}

random.seed(os.urandom(1024))

step_level: int = 0  # pylint: disable=invalid-name

cur_color = "blue"  # pylint: disable=invalid-name


def set_available_color(used_colors: set[str]) -> tuple[str, str]:
    """Set the available color.

    Args:
        used_colors (set[str]): Used prompt colors set of parent process.

    Returns:
        tuple[str, str]: Available color id and color name.
            Returns ("full", "blue") if all colors are used.

    """
    global cur_color  # pylint: disable=W0603 # noqa: PLW0603
    used = set(used_colors)
    unused = list(set(AVAILABLE_STYLES.keys()) - used)
    if not unused:
        cur_color = "blue"
        return "full", "blue"
    if not used:
        cur_color = "blue"
        return "b", "blue"
    choise = random.choice(unused)  # noqa: S311
    cur_color = AVAILABLE_STYLES[choise]
    return choise, AVAILABLE_STYLES[choise]


def push_level() -> None:
    """Increase the output step level."""
    global step_level  # pylint: disable=global-statement # noqa: PLW0603
    step_level += 1


def pop_level() -> None:
    """Decrease the output level."""
    global step_level  # pylint: disable=global-statement # noqa: PLW0603
    step_level -= 1


def sum_level_indent(level: int) -> int:
    """Sum the indent of the level.

    Args:
        level (int): Message level. If it <= -1, it will be set to
        `step_level - level - 1`.

    Returns:
        int: Indent space count.

    """
    if level <= -1:
        level = step_level - level - 1
    return level * 4


def _default_serialize(obj: object) -> list[Any] | str:
    if isinstance(obj, set | frozenset):
        return list(cast("set[Any] | frozenset[Any]", obj))
    if isinstance(obj, bytes):
        try:
            return obj.decode()
        except UnicodeDecodeError:
            return str(obj)
    return repr(obj)


def _is_rich_renderable(obj: object) -> bool:
    return hasattr(obj, "__rich_console__") or hasattr(obj, "__rich__")


def _format_output_type(message: object) -> tuple[str, RenderableType]:
    if isinstance(message, dict | list | tuple | set | frozenset):
        try:
            json_str = json.dumps(
                message,
                indent=2,
                sort_keys=True,
                default=_default_serialize,
            )
            return ("json", json_str)  # noqa: TRY300
        except (TypeError, RecursionError):
            logger.warning("Failed to serialize object to JSON.")
            return ("repr", repr(cast("object", message)))
    msg = str(message) if isinstance(message, str) else repr(message)
    return ("str", escape(msg))


def _format_output(
    message: object,
    method: OutputMethod,
) -> tuple[str, RenderableType]:
    if _is_rich_renderable(message):
        return ("rich", cast("RenderableType", message))

    if method == OutputMethod.RAW:
        msg = message if isinstance(message, str) else repr(message)
        return ("raw", escape(msg))
    if method == OutputMethod.FORMAT_MARKUP:
        return ("markup", str(message))
    if method == OutputMethod.FORMAT_TYPE:
        return _format_output_type(message)
    if method == OutputMethod.FORMAT_MARKDOWN:
        md = Markdown(str(message))
        return ("markdown", md)

    # Internal error. Don't use Rubisco exceptions.
    msg = f"Unknown output method: {method}"
    raise ValueError(msg)


def _convert_tree(
    tree: RUTree[object],
    rich_tree_root: Tree,
    method: OutputMethod,
) -> None:
    """Convert RUTree to rich Tree."""
    for ru_node in tree.children:
        if is_instance(ru_node.value, tuple[object, OutputMethod]):
            node_output, node_method = cast(
                "tuple[object, OutputMethod]",
                ru_node.value,
            )
        else:
            node_output, node_method = ru_node.value, method
        node = rich_tree_root.add(_format_output(node_output, node_method)[1])
        if ru_node.children:
            _convert_tree(ru_node, node, method)


def _output_tree(
    tree: RUTree[object],
    method: OutputMethod,
    ident: int,
) -> None:
    if is_instance(tree.value, tuple[object, OutputMethod]):
        root_output, root_method = cast(
            "tuple[object, OutputMethod]",
            tree.value,
        )
    else:
        root_output, root_method = tree.value, method
    rich_tree = Tree(
        _format_output(root_output, root_method)[1],
        guide_style=cur_color,
    )
    _convert_tree(tree, rich_tree, method)
    rich.print(Padding.indent(rich_tree, ident))


def format_and_output(
    message: object,
    method: OutputMethod,
    end: str = "\n",
    ident: int = sum_level_indent(step_level),
) -> None:
    r"""Format the output message.

    Args:
        message (object): Message object.
        method (OutputMethod): Output method.
        end (str, optional): End of the message. Defaults to '\\n'.
        ident (int, optional): Indent spaces. If OutputMethod is
            RAW, it will be ignored. Defaults to sum_level_indent(step_level).

    """
    if method == OutputMethod.RAW:
        ident = 0

    if isinstance(message, RUTree):
        _output_tree(cast("RUTree[object]", message), method, ident)
        return

    out = _format_output(message, method)
    if out[0] == "json":
        rich.print_json(json=str(out[1]), indent=ident)
    else:
        lines = out[1]
        if isinstance(lines, str):
            lines = lines.splitlines()
            for line_ in lines:
                line = line_.replace("\t", " " * 4)
                rich.print(
                    Padding.indent(_format_output(line, method)[1], ident),
                    end=end,
                )
        else:
            rich.print(Padding.indent(out[1], ident), end=end)


def output_line(
    message: str,
    level: int = -1,
    method: OutputMethod = OutputMethod.FORMAT_MARKUP,
) -> None:
    r"""Output a line message with level.

    Args:
        message (str): Message.
        level (int): Message level. If it <= -1, it will be set to
        `step_level - level - 1`.
        method (OutputMethod, optional): Output method. Defaults to
        OutputMethod.FORMAT_MARKUP.

    """
    if not message:
        return
    indent = sum_level_indent(level)
    format_and_output(message, method=method, ident=indent, end="\n")


def get_prompt(level: int, style1: str = "=>", style2: str = "::") -> Text:
    """Get the prompt of the level.

    Args:
        level (int): Message level.
        style1 (str, optional): Style of level 0. Defaults to "=>".
        style2 (str, optional): Style of other levels. Defaults to "::".

    Returns:
        Text: Prompt text.

    """
    if level <= -1:
        level = step_level - level - 1
    return Text(
        style1 if level == 0 else style2,
        style=cur_color,
    )


def output_step(message: str, level: int = -1) -> None:
    r"""Output a step message.

    Args:
        message (str): Message.
        level (int): Message level. If it <= -1, it will be set to
        `step_level - level - 1`. The effect is as follows:
        ```
            => Level 0 message.
                :: Level 1 message.
                :: Level 1 message.
                    :: Level 2 message.
            => Level 0 message.
        ```

    """
    if message.strip():
        indent = sum_level_indent(level)
        prompt = get_prompt(level).markup

        format_and_output(
            prompt + " " + message,
            method=OutputMethod.FORMAT_MARKUP,
            ident=indent,
        )


def output_error(message: str) -> None:
    """Output an error message.

    Args:
        message (str): Message.

    """
    format_and_output(
        fast_format_str(_("[red]Error: ${{msg}}[/red]"), fmt={"msg": message}),
        method=OutputMethod.FORMAT_MARKUP,
    )


def output_warning(message: str) -> None:
    """Output a warning message.

    Args:
        message (str): Message.

    """
    format_and_output(
        fast_format_str(
            _("[yellow]Warning: ${{msg}}[/yellow]"),
            fmt={"msg": message},
        ),
        method=OutputMethod.FORMAT_MARKUP,
    )


def output_hint(message: str) -> None:
    """Output a hint message.

    Args:
        message (str): Message.

    """
    format_and_output(
        fast_format_str(
            _("[italic][magenta]Hint:[/magenta] ${{msg}}[/italic]"),
            fmt={"msg": message},
        ),
        method=OutputMethod.FORMAT_MARKUP,
    )


def show_exception(  # noqa: C901
    exc: Exception | KeyboardInterrupt,
    *,
    as_warn: bool = False,
) -> None:
    """Show an exception. If it has docurl or hint, show it also.

    Args:
        exc (Exception): Exception object.
        as_warn (bool, optional): Show it as a warning. Defaults to False.

    """
    logger.exception(exc)
    hint = getattr(exc, "hint", None)
    docurl = getattr(exc, "docurl", None)
    message = str(exc)
    typestr = type(exc).__name__

    perror = output_warning if as_warn else output_error
    if isinstance(exc, BeartypeException):
        perror = output_line

    if isinstance(exc, RUError | ValueError | AssertionError):
        if not message:
            message = _("Unknown error.")
        perror(message)
    elif isinstance(exc, KeyboardInterrupt):
        perror(_("Interrupted by user."))
    elif isinstance(exc, OSError):
        perror(message)
    elif isinstance(exc, json5.JSON5DecodeError):
        perror(_("JSON5 decode error."))
        perror(message)
        output_hint(_("Is may caused by a invalid JSON5 configuration file."))
    elif isinstance(exc, KeyError):
        perror(
            fast_format_str(
                _("Missing key: ${{msg}}"),
                fmt={"msg": message},
            ),
        )
        output_hint(_("Is may caused by a invalid configuration file."))
    elif isinstance(exc, SystemExit):
        raise exc
    else:
        perror(
            fast_format_str(
                _("Internal error: ${{type}}: ${{msg}}"),
                fmt={"type": typestr, "msg": message},
            ),
        )

    if hint:
        output_hint(hint)
    if docurl:
        output_hint(fast_format_str(_("See: ${{url}}"), fmt={"url": docurl}))
