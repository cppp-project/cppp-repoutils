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

"""Help messages for Rubisco CommandEventFS Debugger CLI."""

from typing import cast

import rich
from rich.table import Table

from rubisco.cli.output import output_hint
from rubisco.lib.l10n import _

__all__ = ["show_all_helps", "show_help"]

_help_msgs: dict[str, dict[str, str | dict[str, str]]] = {}


def init_helps() -> dict[str, dict[str, str | dict[str, str]]]:
    """Initialize help messages.

    This function MUST be called after L10N is initialized.

    Returns:
        dict[str, dict[str, str | dict[str, str]]]: The help messages.

    """
    return {
        "cd": {
            "short": _("Change the debugger's working directory."),
            "usage": "[green]cd[/green] [italic]\\[PATH][/italic]",
            "args": {
                "path": _(
                    "Change the current directory to [italic]\\[PATH]"
                    "[/italic]. The default [italic]\\[PATH][/italic] is the"
                    " root directory",
                ),
            },
        },
        "cat": {
            "short": _("Display the file's data."),
            "usage": "[green]cat[/green] [bold]<FILE>[/bold]",
            "args": {
                "file": _("The file path to display."),
            },
        },
        "stat": {
            "short": _("Display file or directory status."),
            "usage": "[green]stat[/green] [bold]<FILE>[/bold]",
            "args": {
                "file": _("The file path to display status."),
            },
        },
        "ls": {
            "short": _("List directory contents."),
            "usage": "[green]ls[/green] [italic]\\[PATH][/italic]",
            "args": {
                "path": _(
                    "List the directory contents of [italic]\\[PATH]"
                    "[/italic]. The default [italic]\\[PATH][/italic] is the"
                    " current directory",
                ),
            },
        },
        "python": {
            "short": _("Open a embed IPython shell."),
            "usage": "[green]python[/green]",
        },
        "exit": {
            "short": _("Exit the debugger."),
            "usage": "[green]exit[/green]",
        },
        "help": {
            "short": _("Display information about builtin commands."),
            "usage": "[green]help[/green] [italic]\\[COMMAND][/italic]",
            "args": {
                "command": _(
                    "The command to display help information. If not"
                    " specified, display help information about all"
                    " builtin commands.",
                ),
            },
        },
        "clear": {
            "short": _("Clear the terminal screen and scrollback buffer."),
            "usage": "[green]clear[/green]",
        },
    }


def show_all_helps() -> None:
    """Show all help messages."""
    if not _help_msgs:
        _help_msgs.update(init_helps())

    table = Table(show_header=True, header_style="bold magenta", box=None)
    table.add_column(_("Command"))
    table.add_column(_("Description"))
    for cmd, msg in _help_msgs.items():
        table.add_row(f"[green]{cmd}[/green]", cast("str", msg["short"]))

    rich.print(table)
    rich.print()
    output_hint(
        _(
            "Use [green]help[/green] [bold]<COMMAND>[/] to get more help.",
        ),
    )
    output_hint(
        _(
            '`help` use "[italic][COMMAND][/italic]" for optional arguments. '
            'Use "[bold]<COMMAND>[/bold]" for required arguments.',
        ),
    )


def show_help(cmd: str) -> None:
    """Show help message for a command.

    Args:
        cmd (str): The command to show help message.

    Raises:
        ValueError: If the command is not found.

    """
    if not _help_msgs:
        _help_msgs.update(init_helps())

    if cmd not in _help_msgs:
        msg = f"Command {cmd} not found."
        raise ValueError(msg)

    msg = _help_msgs[cmd]
    rich.print(msg["short"])
    rich.print(_("Usage:") + cast("str", msg["usage"]))
    if msg.get("args"):
        rich.print(_("Arguments:"))
        arg_table = Table(
            show_header=False,
            header_style="bold magenta",
            box=None,
        )
        arg_table.add_column()
        arg_table.add_column()
        for arg, desc in cast("dict[str, str]", msg["args"]).items():
            arg_table.add_row(f"[blue]{arg}[/blue]", desc)
        rich.print(arg_table)
