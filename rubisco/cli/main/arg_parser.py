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

"""Argument for CLI."""

import argparse
from typing import Any

from rubisco.cli.argparse_generator import gen_argparse
from rubisco.cli.cefs_dbg.callback import cefs_callback
from rubisco.cli.main.help_formatter import RUHelpFormatter
from rubisco.cli.main.version_action import CLIVersionAction, version_callback
from rubisco.kernel.command_event.args import (
    Argument,
    Option,
    load_callback_args,
)
from rubisco.kernel.command_event.callback import EventCallback
from rubisco.kernel.command_event.event_file_data import EventFileData
from rubisco.kernel.command_event.event_path import EventPath
from rubisco.kernel.command_event.event_types import (
    EventObjectStat,
    EventObjectType,
)
from rubisco.kernel.command_event.register import EventUnit, register_events
from rubisco.kernel.config_file import config_file
from rubisco.lib.l10n import _

__all__ = [
    "early_arg_parser",
    "get_arg_parser",
    "init_arg_parser",
]


def init_options(options: list[Option[Any]], args: list[Argument[Any]]) -> None:
    """Parse options in '/' and init Rubisco configs.

    Args:
        options (list[Option[Any]]): Options of command line.
        args (list[Argument[Any]]): Arguments of command line.

    """
    opts, __ = load_callback_args(options, args)
    verbose = opts.get("enable-verbose")
    config_file.config["verbose"] = verbose


def init_arg_parser() -> None:
    """Initialize argument parser."""
    EventPath("/").event_object.set_stat(
        EventObjectStat(
            type=EventObjectType.DIRECTORY,
            options=[
                Option[str](
                    name="project-root-dir",
                    title=_("Project root"),
                    description=_("The root directory of Rubisco project."),
                    typecheck=str,
                    aliases=["root"],
                    default=".",
                ),
                Option[str](
                    name="used-prompt-colors",
                    title=_("Used prompt colors (for CLI)."),
                    description=_(
                        "Prompt colors used by rubisco parent process.",
                    ),
                    typecheck=str,
                    default="",
                ),
                Option[bool](
                    name="enable-rubisco-log",
                    title=_("Enable Rubisco log"),
                    description=_(
                        "Allow Rubisco to save log. Do not use this"
                        " option directly. Use `--log`"
                        " to allow Rubisco log. It will be saved"
                        " to `.rubisco/rubisco.log`.",
                    ),
                    typecheck=bool,
                    default=False,
                    ext_attributes={
                        "cli-advanced-options": [
                            {
                                "name": "--log",
                                "help": _("Allow Rubisco to save log."),
                                "action": "store_true",
                            },
                        ],
                    },
                ),
                Option[bool](
                    name="rubisco-debug",
                    title=_("Enable debug mode."),
                    description=_(
                        "Run rubisco in debug mode. "
                        "Don't use this option directly. Use "
                        "`--debug` to enable debug mode. It's"
                        " parsed when Rubisco log system"
                        " initializing.",
                    ),
                    typecheck=bool,
                    default=False,
                    ext_attributes={
                        "cli-advanced-options": [
                            {
                                "name": "--debug",
                                "help": _("Run rubisco in debug mode."),
                                "action": "store_true",
                            },
                        ],
                    },
                ),
                Option[bool](
                    name="enable-verbose",
                    title=_("Verbose"),
                    description=_("Enable verbose output."),
                    typecheck=bool,
                    default=False,
                    ext_attributes={
                        "cli-advanced-options": [
                            {
                                "name": "--verbose",
                                "help": _("Enable verbose output."),
                                "action": "store_true",
                            },
                        ],
                    },
                ),
                Option[bool](
                    name="enable-cefs-debugger",
                    title=_("Run CommandEventFS Debugger"),
                    description=_(
                        "Launch Rubisco CommandEventFS Debugger CLI"
                        " after CEFS initialized.",
                    ),
                    typecheck=bool,
                    default=False,
                    ext_attributes={
                        "cli-advanced-options": [
                            {
                                "name": ["--cefs-debug", "-D"],
                                "help": _(
                                    "Launch Rubisco CommandEventFS Debugger CLI"
                                    " after CEFS initialized.",
                                ),
                                "action": "store_true",
                            },
                        ],
                    },
                ),
                Option[bool](
                    name="use-systemd-style-log",
                    title=_("Use systemd style log format"),
                    description=_(
                        "Use systemd style log output "
                        "format just for fun."
                        "Don't use this option directly. Use "
                        "`--debug` to enable debug mode. It's"
                        " parsed when Rubisco log system"
                        " initializing.",
                    ),
                    typecheck=bool,
                    default=False,
                    ext_attributes={
                        "cli-advanced-options": [
                            {
                                "name": ["--systemd-style-log", "-S"],
                                "help": _(
                                    "Use systemd style log output "
                                    "format just for fun.",
                                ),
                                "action": "store_true",
                            },
                        ],
                    },
                ),
            ],
            dir_callbacks=[
                EventCallback(
                    callback=init_options,
                    description=_(
                        "Parse options in '/' and init Rubisco configs.",
                    ),
                ),
            ],
        ),
    )

    register_events(
        [
            EventUnit(
                name="version",
                stat=EventObjectStat(
                    type=EventObjectType.FILE,
                    description=_("Show version."),
                ),
                file_data=EventFileData(
                    callbacks=[
                        EventCallback(
                            callback=version_callback,
                            description=_("Show Rubisco version."),
                        ),
                    ],
                ),
            ),
            EventUnit(
                name="cefs-debug",
                stat=EventObjectStat(
                    type=EventObjectType.FILE,
                    description=_("Launch CommandEventFS Debugger."),
                ),
                file_data=EventFileData(
                    callbacks=[
                        EventCallback(
                            callback=cefs_callback,
                            description=_(
                                "Launch Rubisco CommandEventFS Debugger CLI.",
                            ),
                        ),
                    ],
                ),
            ),
            EventUnit(
                name="ext",
                stat=EventObjectStat(
                    type=EventObjectType.DIRECTORY,
                    description=_("Extension directory."),
                ),
            ),
        ],
    )


def get_arg_parser() -> argparse.ArgumentParser:
    """Generate a new argument parser from CommandEventFS.

    Returns:
        argparse.ArgumentParser: The generated argument parser.

    """
    arg_parser = argparse.ArgumentParser(
        description="Rubisco CLI",
        formatter_class=RUHelpFormatter,
        allow_abbrev=True,
    )

    arg_parser.register("action", "version", CLIVersionAction)

    # For "rubisco --version".
    arg_parser.add_argument(
        "-v",
        "--version",
        action="version",
        version="",
    )
    gen_argparse(EventPath("/"), arg_parser)

    return arg_parser


# Early argument parser.
early_arg_parser = argparse.ArgumentParser(
    description="Rubisco CLI",
    add_help=False,
    allow_abbrev=True,
    formatter_class=RUHelpFormatter,
)

# For "rubisco --version".
early_arg_parser.add_argument(
    "--root",
    type=str,
    help=_("Project root directory."),
    action="store",
    dest="root_directory",
)

# For "rubisco --used-colors=COLORS"
early_arg_parser.add_argument(
    "--used-prompt-colors",
    type=set,
    help=_("Prompt colors used by rubisco parent process."),
    action="store",
    default=set(),
    dest="used_prompt_colors",
)
