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

"""C++ Plus Rubisco CLI main entry point."""

from __future__ import annotations

import atexit
import os
import sys
from pathlib import Path

import colorama

from rubisco.cli.main.arg_parser import (
    early_arg_parser,
    get_arg_parser,
    init_arg_parser,
)
from rubisco.cli.main.builtin_cmds import register_builtin_cmds
from rubisco.cli.main.extman_cmds import register_extman_cmds
from rubisco.cli.main.ktrigger import RubiscoKTrigger
from rubisco.cli.main.log_cleaner import clean_logfile
from rubisco.cli.main.project_config import load_project
from rubisco.cli.output import output_step, set_available_color, show_exception
from rubisco.config import (
    APP_VERSION,
)
from rubisco.lib.exceptions import RUNotRubiscoProjectError
from rubisco.lib.l10n import _
from rubisco.lib.log import logger
from rubisco.lib.variable.builtin_vars import init_builtin_vars
from rubisco.lib.variable.fast_format_str import fast_format_str
from rubisco.lib.variable.utils import make_pretty
from rubisco.shared.extension import load_all_extensions
from rubisco.shared.ktrigger import (
    bind_ktrigger_interface,
)

__all__ = ["main"]


def on_exit() -> None:
    """Reset terminal color."""
    sys.stdout.write(colorama.Fore.RESET)
    sys.stdout.flush()


atexit.register(on_exit)


def parse_early_arguments() -> None:
    """Parse early arguments."""
    early_args = early_arg_parser.parse_known_args()[0]

    set_available_color(early_args.used_prompt_colors)

    root_directory: str | None = early_args.root_directory
    if root_directory is not None:
        rootdir = Path(root_directory).absolute()
        output_step(
            fast_format_str(
                _("Entering directory ${{path}} ..."),
                fmt={"path": make_pretty(rootdir)},
            ),
        )
        os.chdir(rootdir)


def main() -> None:
    """Rubisco main entry point."""
    try:
        init_builtin_vars()
        clean_logfile()
        logger.info("Rubisco CLI version %s started.", str(APP_VERSION))
        colorama.init()
        bind_ktrigger_interface("rubisco", RubiscoKTrigger())
        init_arg_parser()
        load_all_extensions()

        # Register built-in command lines.
        register_builtin_cmds()
        register_extman_cmds()

        parse_early_arguments()

        try:
            load_project()
            no_project_mode = False
        except RUNotRubiscoProjectError:
            no_project_mode = True

        if no_project_mode:
            logger.debug("Running in no project mode.")

        arg_parser = get_arg_parser()
        args = arg_parser.parse_args()

        args.callback(args)
        sys.exit(0)

    except SystemExit as exc:
        raise exc from None  # Do not show traceback.
    except KeyboardInterrupt as exc:
        show_exception(exc)
        sys.exit(1)
    except Exception as exc:  # pylint: disable=broad-except # noqa: BLE001
        logger.critical("An unexpected error occurred.", exc_info=True)
        show_exception(exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
