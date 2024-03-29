# -*- coding: utf-8 -*-
# -*- mode: python -*-
# vi: set ft=python :

# Copyright (C) 2024 The C++ Plus Project.
# This file is part of the cppp-repoutils.
#
# cppp-repoutils is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 3 of the License,
# or (at your option) any later version.
#
# cppp-repoutils is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
cppp-repoutils CLI main entry point.
"""

import atexit
import sys

from cppp_repoutils.cli import main
from cppp_repoutils.utils.log import logger
from cppp_repoutils.constants import APP_VERSION_STRING


def on_exit() -> None:
    """
    Exit handler.
    """

    logger.debug("on_exit() called.")
    logger.info("cppp-repoutils running finished.")


atexit.register(on_exit)

if __name__ == "__main__":
    logger.info(
        "C++ Plus Repository Utilities %s started.",
        APP_VERSION_STRING,
    )
    sys.exit(main())
