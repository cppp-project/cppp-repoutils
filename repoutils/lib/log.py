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
Logging system.
"""

import logging
import sys

from repoutils.config import (
    APP_NAME,
    DEFAULT_CHARSET,
    LOG_FILE,
    LOG_FORMAT,
    LOG_LEVEL,
)

__all__ = ["logger"]

# The global logger.
logger = logging.getLogger(APP_NAME)

# Initialize the global logger.

logger.setLevel(LOG_LEVEL)

if "--debug" in sys.argv:  # Don't use argparse here.
    logger_handler = logging.FileHandler(LOG_FILE, encoding=DEFAULT_CHARSET)
    logger_handler.setLevel(LOG_LEVEL)

    logger_formatter = logging.Formatter(LOG_FORMAT)
    logger_handler.setFormatter(logger_formatter)

    logger.addHandler(logger_handler)
else:  # Disable logging.
    logger.handlers.clear()
    logger.addHandler(logging.NullHandler())


if __name__ == "__main__":
    print(f"{__file__}: {__doc__.strip()}")

    print("hint: Run with '--debug' to enable logging.")

    # Test.
    logger.debug("DEBUG")
    logger.info("INFO")
    logger.warning("WARNING")
    logger.error("ERROR")
    logger.critical("CRITICAL")
    try:
        raise RuntimeError("Test exception.")
    except RuntimeError:
        logger.exception("EXCEPTION")
        logger.warning("Warning with exception.", exc_info=True)
    logger.info("END")
