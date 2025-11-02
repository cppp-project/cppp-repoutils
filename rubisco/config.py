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

"""Module configuration."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from rubisco.lib.command import command
from rubisco.lib.version import Version

# Application basic configurations.
APP_NAME = "rubisco"
APP_VERSION = Version((0, 1, 0))
MINIMUM_PYTHON_VERSION = (3, 11)

# Generated constants.
STDOUT_IS_TTY = sys.stdout.isatty()
PROGRAM_PATH = Path(sys.argv[0]).resolve()  # pylint: disable=C0103
if not sys.argv[0]:
    PROGRAM_PATH = Path(__file__).resolve().parent  # pylint: disable=C0103 # type: ignore[arg-type]

# If the program is running in a packed environment. (e.g. PyInstaller)
IS_PACKED = getattr(sys, "frozen", False) or hasattr(sys, "_MEIPASS")

PYTHON_PATH = None if IS_PACKED else Path(sys.executable).resolve()

RUBISCO_COMMAND = (
    command(str(PROGRAM_PATH))
    if IS_PACKED
    else command(
        [str(PYTHON_PATH), str(PROGRAM_PATH)],
    )
)

PROGRAM_DIR = PROGRAM_PATH.parent.absolute()

# Global directories on Windows.
if os.name == "nt":
    RUBISCO_GLOBAL_LOCAL_DIR = PROGRAM_DIR
    RUBISCO_GLOBAL_CONFIG_DIR = PROGRAM_DIR / "config"
    GLOBAL_CONFIG_FILE = RUBISCO_GLOBAL_CONFIG_DIR / "config.json"
    GLOBAL_EXTENSIONS_VENV_DIR = RUBISCO_GLOBAL_LOCAL_DIR / "extensions"
else:
    # Global directories on Linux and macOS.
    RUBISCO_GLOBAL_LOCAL_DIR = Path("/usr/local/lib") / APP_NAME
    RUBISCO_GLOBAL_CONFIG_DIR = Path("/etc") / APP_NAME
    GLOBAL_CONFIG_FILE = RUBISCO_GLOBAL_CONFIG_DIR / "config.json"
    GLOBAL_EXTENSIONS_VENV_DIR = RUBISCO_GLOBAL_LOCAL_DIR / "extensions"

# I18n configurations.
TEXT_DOMAIN = APP_NAME
DEFAULT_CHARSET = "UTF-8"

# Miscellaneous configurations.
TIMEOUT = 15
COPY_BUFSIZE = 1024 * 1024 if os.name == "nt" else 64 * 1024

# Extension configuration.
VALID_EXTENSION_NAME = r"^[A-Za-z0-9_\-.]+$"
VENV_LOCK_FILENAME = "venv.lock"
DB_FILENAME = f"{APP_NAME}.db"

# RUXR configurations.
RUXR_POOL_RELEASE_FILE_PATH = "/pool/Release.json"
RUXR_PACKAGE_METADATA_FILE_PATH = f"/pool/${{package}}/{APP_NAME}.json"

# Workspace configurations.
WORKSPACE_CONFIG_DIR = Path(f".{APP_NAME}")
WORKSPACE_CONFIG_FILE = WORKSPACE_CONFIG_DIR / "config.json"
WORKSPACE_EXTENSIONS_VENV_DIR = WORKSPACE_CONFIG_DIR / "extensions"
WORKSPACE_REPO_CONFIG_NAME = "repo.json"
WORKSPACE_REPO_CONFIG = Path(WORKSPACE_REPO_CONFIG_NAME)

# Extension installation directory. Without venv suffix.
# Valid directory name is
# GLOBAL/USER/WORKSPACE_EXTENSIONS_VENV_DIR / EXTENSION_NAME.
if os.name == "nt":
    EXTENSIONS_DIR = Path("Lib") / APP_NAME
else:
    EXTENSIONS_DIR = Path("lib") / APP_NAME

# User configurations.
Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
if sys.platform == "win32":
    USER_LOCAL_DIR = Path(
        os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local"),
    )
    RUBISCO_USER_LOCAL_DIR = USER_LOCAL_DIR / APP_NAME
    USER_CONFIG_DIR = Path(
        os.getenv("APPDATA", Path.home() / "AppData" / "Roaming"),
    )
    RUBISCO_USER_CONFIG_DIR = USER_CONFIG_DIR / APP_NAME
else:
    USER_LOCAL_DIR = Path.home() / ".local" / "share"
    RUBISCO_USER_LOCAL_DIR = USER_LOCAL_DIR / APP_NAME
    USER_CONFIG_DIR = Path.home() / ".config"
    RUBISCO_USER_CONFIG_DIR = USER_CONFIG_DIR / APP_NAME
USER_CONFIG_FILE = RUBISCO_USER_CONFIG_DIR / "config.json"
USER_EXTENSIONS_VENV_DIR = RUBISCO_USER_LOCAL_DIR / "extensions"

# Logging configurations.
# We don't need to absolute the path because rubisco supports '--root'
# option.
LOG_FILE = WORKSPACE_CONFIG_DIR / f"{APP_NAME}.log"
LOG_FORMAT = "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s"
LOG_REGEX = r"\[(.*)\] \[(.*)\] \[(.*)\] (.*)"
LOG_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_LEVEL = "DEBUG"
PIP_LOG_FILE = WORKSPACE_CONFIG_DIR / "pip.log"
DEFAULT_LOG_KEEP_LINES = 5000

# RuBP packaging configurations.
RUBP_METADATA_FILE_NAME = f"{APP_NAME}.json"
RUBP_REQUIREMENTS_FILE_NAME = "requirements.txt"
RUBP_LICENSE_FILE_NAME = "LICENSE"
RUBP_README_FILE_NAME = "README.md"
RUBP_RESOURCE_DIR_NAME = "res"
