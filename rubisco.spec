# -*- mode: python -*-
# vi: set ft=python :

# Copyright (C) 2025 The C++ Plus Project.
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

"""Build script for PyInstaller."""

from PyInstaller.building.api import COLLECT, EXE, PYZ  # type: ignore[import]
from PyInstaller.building.build_main import Analysis  # type: ignore[import]
from PyInstaller.utils.hooks import collect_submodules

DEBUG = False

hiddenimports: list[str] = []
hiddenimports += collect_submodules("rubisco.shared")
hiddenimports += collect_submodules("rubisco.config")
hiddenimports += collect_submodules("zoneinfo")


a = Analysis(
    ["rubisco/__main__.py"],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=2,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="rubisco",
    debug=DEBUG,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="rubisco.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="rubisco",
)
