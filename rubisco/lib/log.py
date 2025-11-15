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

"""Logging system."""

import logging
import sys
from pathlib import Path

import rich
import rich.logging
from rich.console import Console
from rich.text import Text

from rubisco.config import (
    APP_NAME,
    DEFAULT_CHARSET,
    LOG_FILE,
    LOG_FORMAT,
    LOG_LEVEL,
    LOG_TIME_FORMAT,
)

__all__ = ["logger", "rubisco_get_logger"]


class _SystemdStyleHandler(logging.Handler):
    """A logging handler that make log format like systemd."""

    def _indent(
        self,
        console: Console,
        prefix: Text,
        message: str,
        width: int,
    ) -> Text:
        text_obj = Text()
        text_obj.append(prefix)
        prefix_length = console.measure(prefix).maximum
        indent_spaces = " " * 9
        words = message.split()
        current_line_length = prefix_length

        for word in words:
            word_length = len(word) + 1

            if current_line_length + word_length > width:
                text_obj.append(Text(f"\n{indent_spaces}{word}", style="bold"))
                current_line_length = 4 + word_length
            else:
                text_obj.append(Text(f" {word}", style="bold"))
                current_line_length += word_length

        return text_obj

    def emit(self, record: logging.LogRecord) -> None:
        level = record.levelno
        if level >= logging.FATAL:
            err = Text.from_markup("\\[[red]FATAL[/red]]")
        elif level >= logging.ERROR:
            err = Text.from_markup("\\[[red]FAILED[/red]]")
        elif level >= logging.WARNING:
            err = Text.from_markup("\\[[yellow] WARN [/yellow]]")
        elif level >= logging.INFO:
            err = Text.from_markup("\\[[green]  OK  [/green]]")
        else:
            return
        console = Console(file=sys.stderr)
        indented_msg = self._indent(
            console,
            err,
            record.getMessage(),
            int(console.width * 0.9),
        )
        console.print(indented_msg)


def rubisco_get_logger(name: str = APP_NAME) -> logging.Logger:
    """Get the logger.

    Args:
        name (str, optional): The name of the logger. Defaults to APP_NAME.

    Returns:
        logging.Logger: The logger.

    """
    ru_logger = logging.getLogger(name)
    ru_logger.setLevel(LOG_LEVEL)
    _init_log_handler(ru_logger)
    return ru_logger


def _init_log_handler(logger_: logging.Logger) -> None:
    logger_.addHandler(logging.NullHandler())

    if "--log" in sys.argv:
        if not Path(LOG_FILE).parent.exists():
            LOG_FILE.parent.mkdir(exist_ok=True)
        handler = logging.FileHandler(LOG_FILE, encoding=DEFAULT_CHARSET)
        handler.setLevel(LOG_LEVEL)

        formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_TIME_FORMAT)
        handler.setFormatter(formatter)

        logger_.addHandler(handler)
    if "--debug" in sys.argv:  # Don't use argparse here.
        handler = rich.logging.RichHandler(
            level=LOG_LEVEL,
            console=rich.get_console(),
        )
        logger_.addHandler(handler)
    if "--systemd-style-log" in sys.argv:
        handler = _SystemdStyleHandler(level=logging.INFO)
        logger_.addHandler(handler)


# The global logger.
logger = rubisco_get_logger()
