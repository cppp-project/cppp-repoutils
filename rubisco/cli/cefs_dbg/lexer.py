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

"""Rubisco CEFS debug command lexer."""

from collections.abc import Callable

from prompt_toolkit.document import Document
from prompt_toolkit.formatted_text import FormattedText, OneStyleAndTextTuple
from prompt_toolkit.formatted_text.base import StyleAndTextTuples
from prompt_toolkit.lexers import Lexer
from prompt_toolkit.styles import Style

from rubisco.kernel.command_event.event_path import EventPath

__all__ = ["CEFSDebuggerCLICommandLexer"]

KEYWORDS = {
    "cd",
    "cat",
    "stat",
    "ls",
    "exit",
    "help",
    "clear",
    "python",
}


class CEFSDebuggerCLICommandLexer(Lexer):
    """Rubisco CEFS debugger CLI command lexer."""

    def __init__(self) -> None:
        """Initialize the CEFSDebuggerCLICommandLexer class."""
        self.style = Style.from_dict(
            {
                "prompt-str": "ansigreen",
                "prompt-path": "underline ansipurple",
                "command": "ansigreen",
                "invalid": "ansired",
                "string": "ansiyellow",
                "comment": "ansibrightblack",
                "file": "ansipurple",
                "alias": "ansicyan",
                "mountpoint": "underline ansipurple",
            },
        )

    def _lex_arg(self, text: str) -> str:
        ep = EventPath(text)
        if ep.is_file() or ep.is_dir():
            return "class:file"
        if ep.is_alias():
            return "class:alias"
        if ep.is_mount_point():
            return "class:mountpoint"
        return ""

    def _lex_args(
        self,
        args: str,
        fragments: list[OneStyleAndTextTuple],
    ) -> None:
        tokens = args.split(" ")
        if len(tokens) == 0:
            return

        if tokens[0] in KEYWORDS:
            fragments.append(("class:command", tokens[0]))
        else:
            fragments.append(("class:invalid", tokens[0]))

        fragments.extend(
            (
                self._lex_arg(token),
                " " + token,
            )
            for token in tokens[1:]
        )

    def lex_document(
        self,
        document: Document,
    ) -> Callable[[int], StyleAndTextTuples]:
        """Lex document.

        Args:
            document (Document): The document to lex.

        Returns:
            Callable[[int], StyleAndTextTuples]: The lexer function.

        """

        def get_line(lineno: int) -> StyleAndTextTuples:
            orig_line = document.lines[lineno]
            fragments: list[OneStyleAndTextTuple] = []
            line = orig_line.lstrip()
            lspaces = orig_line[: len(orig_line) - len(line)]

            if lspaces:
                fragments.append(("", lspaces))

            if line.startswith("#"):
                fragments.append(("class:comment", line))
                return FormattedText(fragments)

            self._lex_args(line, fragments)
            return FormattedText(fragments)

        return get_line
