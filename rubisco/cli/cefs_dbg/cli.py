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

"""Rubisco CLI for CommandEventFS debugging."""

import shlex
from pathlib import Path
from traceback import FrameSummary
from typing import Any

import IPython
import rich
from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.history import InMemoryHistory

from rubisco.cli.cefs_dbg.completer import CEFSDebuggerCLICompleter
from rubisco.cli.cefs_dbg.helpmsg import show_all_helps, show_help
from rubisco.cli.cefs_dbg.lexer import CEFSDebuggerCLICommandLexer
from rubisco.kernel.command_event.args import Option
from rubisco.kernel.command_event.callback import EventCallback
from rubisco.kernel.command_event.event_file_data import EventFileData
from rubisco.kernel.command_event.event_path import EventPath
from rubisco.kernel.command_event.event_types import (
    EventObjectType,
    get_event_object_type_string,
)
from rubisco.lib.exceptions import RUError, RUValueError
from rubisco.lib.l10n import _
from rubisco.lib.log import logger
from rubisco.lib.variable.fast_format_str import fast_format_str
from rubisco.lib.variable.utils import make_pretty


class RubiscoCEFSDebuggerCLI:
    """Rubisco CLI for CommandEventFS debugging."""

    lexer: CEFSDebuggerCLICommandLexer
    prompt_session: PromptSession[str]
    cwd: EventPath

    def __init__(self) -> None:
        """Initialize the RubiscoCEFSDebuggerCLI class."""
        self.lexer = CEFSDebuggerCLICommandLexer()
        self.cwd = EventPath("/")

        self.prompt_session = PromptSession(
            history=InMemoryHistory(),
            lexer=self.lexer,
            completer=CEFSDebuggerCLICompleter(self),
            # Activate completion only when the user types tab.
            complete_while_typing=False,
        )

    def run(self) -> None:
        """Run the RubiscoCEFSDebuggerCLI class."""
        logger.info("Rubisco CEFS Debugger CLI is running.")
        rich.print(
            _(
                "[bold]Welcome to Rubisco Command Event "
                "Filesystem Debugger.\nType '[green]help"
                "[/green]' for help.[/bold]",
            ),
        )
        while True:
            try:
                prompt = FormattedText(
                    [
                        ("class:prompt-str", "CEFS Debug"),
                        ("", ":"),
                        (
                            "class:prompt-path",
                            f"{self.cwd.normpath().as_posix()}",
                        ),
                        ("", "$ "),
                    ],
                )
                text = self.prompt_session.prompt(
                    prompt,
                    style=self.lexer.style,
                )
            except EOFError:
                rich.print("[bold]EOF[/bold]")
                break
            except KeyboardInterrupt:
                continue

            if not text:
                continue
            try:
                self._parse(text)
            except (SystemExit, KeyboardInterrupt, EOFError) as exc:
                logger.info("Exiting Rubisco CEFS Debugger CLI.")
                raise SystemExit from exc
            except RUError as exc:
                logger.exception("Error while executing command.")
                rich.print(f"[red]{exc}[/red]")

    def _parse(self, cmdline: str) -> None:  # noqa: C901
        tokens = shlex.split(cmdline)
        if not tokens:
            return
        cmd = tokens[0]
        rest = tokens[1:]
        if cmd == "exit":
            raise SystemExit
        if cmd.startswith("#"):
            return
        if cmd == "clear":
            self.clear(rest)
        elif cmd == "cd":
            self.cd(rest)
        elif cmd == "ls":
            self.ls(rest)
        elif cmd == "cat":
            self.cat(rest)
        elif cmd == "stat":
            self.stat(rest)
        elif cmd == "python":
            self.python(rest)
        elif cmd == "help":
            self.help(rest)
        else:
            rich.print(
                fast_format_str(
                    _("Command not found: ${{cmd}}"),
                    fmt={
                        "cmd": cmd,
                    },
                ),
            )

    def cd(self, args: list[str]) -> None:
        """`cd` command.

        Args:
            args (list[str]): The arguments of `cd` command.

        """
        if not args:
            self.cwd = EventPath("/")
            return
        if len(args) > 1:
            msg = f"cd: {_('Too many arguments.')}"
            raise RUError(msg)
        path = self.cwd.joinpath(args[0])
        if not path.exists():
            msg = f"cd: {_('No such file or directory.')}"
            raise RUError(msg)
        if not path.is_dir():
            msg = f"cd: {_('Not a directory.')}"
            raise RUError(msg)
        self.cwd = path

    def ls(self, args: list[str]) -> None:
        """`ls` command.

        Args:
            args (list[str]): The arguments of `ls` command.

        """
        if len(args) > 1:
            for arg in args:
                self.ls([arg])

        path = self.cwd if not args else self.cwd.joinpath(args[0])
        for ep in path.iterpath():
            stat = ep.stat()
            if stat.type == EventObjectType.DIRECTORY:
                rich.print(f"[blue]{ep.name}[/blue]", end="\t")
            elif stat.type == EventObjectType.FILE:
                rich.print(ep.name, end="\t")
            elif stat.type == EventObjectType.ALIAS:
                color = "lightblue" if ep.exists() else "red"
                rich.print(f"[{color}]{ep.name}[/{color}]", end="\t")
            elif stat.type == EventObjectType.MOUNT_POINT:
                rich.print(
                    f"[underline white]{ep.name}[/underline white]",
                    end="\t",
                )
            else:
                msg = f"Unknown event type {stat.type}, this shouldn't happen."
                raise ValueError(msg)
        rich.print()

    def _cat_args(self, data: EventFileData) -> None:
        if isinstance(data.args, list):
            rich.print(_("Arguments:"))
            for arg in data.args:
                rich.print(f"\t{arg.name}({arg.typecheck}): {arg.description}")
            if not data.args:
                rich.print(f"\t[gray50 italic]{_('None.')}[/gray50 italic]")
        else:
            rich.print(_("Dynamic Arguments:"))
            rich.print(f"\t{data.args.name}: {data.args.description}")
            rich.print(
                fast_format_str(
                    "\t" + _("From ${{mincount}} to ${{maxcount}}."),
                    fmt={
                        "mincount": str(data.args.mincount),
                        "maxcount": (
                            str(data.args.maxcount)
                            if data.args.maxcount != -1
                            else _("unlimited")
                        ),
                    },
                ),
            )

    def _find_source(self, stacktrace: list[FrameSummary]) -> tuple[str, int]:
        for frame in reversed(stacktrace):
            path = Path(frame.filename)
            if path.exists():
                return str(path), frame.lineno or 0
        return _("Unknown."), -1

    def _cat_callbacks(self, callbacks: list[EventCallback]) -> None:
        rich.print(_("Callbacks:"))
        for idx, callback in enumerate(callbacks):
            rich.print(f"\t[{idx}]: {callback.description}")
            rich.print(
                "\t\t"
                + fast_format_str(
                    _("Function: ${{repr}}"),
                    fmt={"repr": repr(callback.callback)},
                ),
            )
            if callback.stacktrace:
                src, lineno = self._find_source(callback.stacktrace)
                if lineno == -1:
                    src = _("Unknown.")
            else:
                src = _("Unknown.")
                lineno = -1
            src = f"{make_pretty(src)}:{lineno}" if lineno != -1 else src
            rich.print(
                "\t\t"
                + fast_format_str(
                    _("Source: ${{src}}"),
                    fmt={"src": src},
                ),
            )
        if not callbacks:
            rich.print(f"\t[gray50 italic]{_('None.')}[/gray50 italic]")

    def cat(self, args: list[str]) -> None:
        """`cat` command.

        Args:
            args (list[str]): The arguments of `cat` command.

        """
        if not args:
            msg = _("No file specified.")
            raise RUError(msg)
        if len(args) > 1:
            msg = _("Too many arguments.")
            raise RUError(msg)

        path = self.cwd.joinpath(args[0]).normpath()
        if not path.exists():
            msg = fast_format_str(
                _("No such file or directory: ${{path}}"),
                fmt={"path": path.as_posix()},
            )
            raise RUError(msg)
        if not path.is_file():
            msg = _("Not a file.")
            raise RUError(msg)
        data = path.read()
        if not data:
            msg = "File is empty, this should never happen."
            raise ValueError(msg)

        self._cat_args(data)
        self._cat_callbacks(data.callbacks)

    def clear(self, args: list[str]) -> None:
        """`clear` command.

        Args:
            args (list[str]): The arguments of `clear` command.

        """
        if args:
            msg = _("Too many arguments.")
            raise RUError(msg)
        console = rich.get_console()
        if console.file.isatty():
            console.file.write("\x1b[H\x1b[2J\x1b[3J")

    def _list_options(self, options: list[Option[Any]]) -> None:
        rich.print(_("Options:"))
        for option in options:
            rich.print(f"\t[blue]{option.name}[/]: {option.title}")
            rich.print(
                "\t\t"
                + fast_format_str(
                    _("Description: [yellow]${{description}}[/yellow]"),
                    fmt={"description": option.description},
                ),
            )
            rich.print(
                "\t\t"
                + fast_format_str(
                    _("Type: [green]${{type}}[/green]"),
                    fmt={"type": option.typecheck.__name__},
                ),
            )
            if option.aliases:
                rich.print(
                    "\t\t"
                    + fast_format_str(
                        _("Aliases: [blue]${{aliases}}[/blue]"),
                        fmt={
                            "aliases": "[/blue], [blue]".join(option.aliases),
                        },
                    ),
                )
            if option.default:
                rich.print(
                    "\t\t"
                    + fast_format_str(
                        _("Default value: ${{default}}"),
                        fmt={"default": repr(option.default)},
                    ),
                )
            if option.ext_attributes:
                rich.print(
                    "\t\t"
                    + fast_format_str(
                        _("Extra attributes: ${{ext_attributes}}"),
                        fmt={
                            "ext_attributes": repr(option.ext_attributes),
                        },
                    ),
                )
            try:
                if option.get():
                    rich.print(
                        "\t\t"
                        + fast_format_str(
                            _("Current value: ${{value}}"),
                            fmt={"value": repr(option.get())},
                        ),
                    )
            except RUValueError:
                pass

    def stat(self, args: list[str]) -> None:
        """`stat` command.

        Args:
            args (list[str]): The arguments of `status` command.

        """
        if not args:
            msg = _("No file specified.")
            raise RUError(msg)
        if len(args) > 1:
            msg = _("Too many arguments.")
            raise RUError(msg)

        path = self.cwd.joinpath(args[0]).normpath()
        if not path.exists():
            msg = fast_format_str(
                _("No such file or directory: ${{path}}"),
                fmt={"path": path.as_posix()},
            )
            raise RUError(msg)

        stat = path.stat()

        if path.is_alias():
            _str_alias = f"-> {make_pretty(stat.alias_to)}"
        else:
            _str_alias = ""
        rich.print(
            fast_format_str(
                _("File: ${{path}} ${{alias_to}}"),
                fmt={"path": make_pretty(path), "alias_to": _str_alias},
            ),
        )
        rich.print(
            fast_format_str(
                _("Type: ${{type}}"),
                fmt={"type": get_event_object_type_string(stat.type)},
            ),
        )
        rich.print(
            fast_format_str(
                _("Description: [yellow]${{description}}[/yellow]"),
                fmt={"description": stat.description},
            ),
        )
        if path.is_mount_point():
            rich.print(
                fast_format_str(
                    _("Mount point: ${{path}}"),
                    fmt={"mount_point": make_pretty(stat.mount_to)},
                ),
            )
        if path.is_dir():
            self._cat_callbacks(stat.dir_callbacks)
        self._list_options(stat.options)

    def python(
        self,
        args: list[str],  # noqa: ARG002 # pylint: disable=W0613
    ) -> None:
        """`python` command.

        Args:
            args (list[str]): The arguments of `python` command.

        """
        try:
            IPython.embed()  # type: ignore[call-arg]
        except BaseException as exc:
            msg = fast_format_str(
                _("Error while executing Python code: ${{error}}"),
                fmt={"error": str(exc)},
            )
            raise RUError(msg) from exc

    def help(self, args: list[str]) -> None:
        """`help` command.

        Args:
            args (list[str]): The arguments of `help` command.

        """
        if len(args) > 1:
            msg = _("Too many arguments.")
            raise RUError(msg)
        if args:
            show_help(args[0])
        else:
            show_all_helps()
