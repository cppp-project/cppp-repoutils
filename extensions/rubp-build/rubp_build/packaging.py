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

"""RuBP packaging."""

import json
import tomllib
from pathlib import Path
from typing import cast

from rubisco.config import (
    APP_NAME,
    DEFAULT_CHARSET,
    RUBP_LICENSE_FILE_NAME,
    RUBP_METADATA_FILE_NAME,
    RUBP_README_FILE_NAME,
    RUBP_REQUIREMENTS_FILE_NAME,
)
from rubisco.shared.api.archive import compress
from rubisco.shared.api.kernel import RUConfiguration
from rubisco.shared.api.l10n import _
from rubisco.shared.api.variable import (
    fast_format_str,
    get_dict_check,
    make_pretty,
    type_assert,
)
from rubisco.shared.ktrigger import IKernelTrigger, call_ktrigger

from rubp_build.logger import logger
from rubp_build.metadata import RUBPMatadata

__all__ = ["RuBP"]


class RuBP:
    """RuBP packaging utils."""

    config: RUConfiguration
    metadata: RUBPMatadata
    bindir: Path
    readme: Path | None
    license: Path | None
    distdir: Path
    version: str

    def __init__(self, config: RUConfiguration) -> None:
        """Initialize RuBP."""
        self.config = config
        self.metadata = RUBPMatadata.from_json(config)
        self.bindir = Path(
            cast(
                "str",
                get_dict_check(
                    config.config,
                    "rubp-bindir",
                    default=".bindir",
                    valtype=str,
                ),
            ),
        )
        readme = cast(
            "str",
            get_dict_check(
                config.config,
                "rubp-readme",
                default="",
                valtype=str,
            ),
        )
        self.readme = Path(readme) if readme else None
        license_ = cast(
            "str",
            get_dict_check(
                config.config,
                "rubp-license",
                default="",
                valtype=str,
            ),
        )
        self.license = Path(license_) if license_ else None
        distdir = cast(
            "str",
            get_dict_check(
                config.config,
                "rubp-distdir",
                default="dist",
                valtype=str,
            ),
        )
        self.distdir = Path(distdir)
        self.version = cast(
            "str",
            get_dict_check(
                config.config,
                "version",
                default="0.0.0",
                valtype=str,
            ),
        )

    def get_requirements_txt(self) -> tuple[str, Path | None]:
        """Get requirements.txt data."""
        requirements_txt = self.config.path.parent / "requirements.txt"
        pyproject_toml = self.config.path.parent / "pyproject.toml"
        if requirements_txt.is_file():
            res_ = ""
            with requirements_txt.open(encoding=DEFAULT_CHARSET) as f:
                for line in f:
                    if line.lstrip().startswith("rubisco"):
                        continue
                    res_ += line
            return (res_, requirements_txt)

        if pyproject_toml.is_file():
            with pyproject_toml.open("rb") as f:
                pyproject_toml_data = tomllib.load(f)
                deps: list[str] = pyproject_toml_data.get("project", {}).get(
                    "dependencies",
                    "",
                )
                type_assert(deps, list[str])
                res: list[str] = []
                for dep in deps:
                    if dep.lstrip().startswith(APP_NAME):
                        continue
                    res.append(dep)
                if deps:
                    return "\n".join(res), pyproject_toml

        return "", None

    def get_readme(self) -> tuple[str, Path | None]:
        """Get readme data."""
        if self.readme:
            return self.readme.read_text(encoding=DEFAULT_CHARSET), self.readme
        readme_md = self.config.path.parent / "README.md"
        readme_txt = self.config.path.parent / "README.txt"
        readme = self.config.path.parent / "README"
        if readme_md.is_file():
            return readme_md.read_text(encoding=DEFAULT_CHARSET), readme_md
        if readme_txt.is_file():
            return readme_txt.read_text(encoding=DEFAULT_CHARSET), readme_txt
        if readme.is_file():
            return readme.read_text(encoding=DEFAULT_CHARSET), readme
        logger.warning("No readme file found.")
        call_ktrigger(
            IKernelTrigger.on_warning,
            message=_("No readme file found."),
        )
        return "", None

    def get_license(self) -> tuple[str, Path | None]:
        """Get license data."""
        if self.license:
            return (
                self.license.read_text(encoding=DEFAULT_CHARSET),
                self.license,
            )
        license_md = self.config.path.parent / "LICENSE.md"
        license_txt = self.config.path.parent / "LICENSE.txt"
        license_ = self.config.path.parent / "LICENSE"
        copying = self.config.path.parent / "COPYING"
        if license_md.is_file():
            return license_md.read_text(encoding=DEFAULT_CHARSET), license_md
        if license_txt.is_file():
            return license_txt.read_text(encoding=DEFAULT_CHARSET), license_txt
        if license_.is_file():
            return license_.read_text(encoding=DEFAULT_CHARSET), license_
        if copying.is_file():
            return copying.read_text(encoding=DEFAULT_CHARSET), copying
        logger.warning("No license file found.")
        call_ktrigger(
            IKernelTrigger.on_warning,
            message=_("No license file found."),
        )
        return "", None

    def pack(self) -> None:
        """Pack project."""
        logger.info("Packing project %s", self.metadata.name)
        logger.info("rubp: %s", self)

        self.distdir.mkdir(parents=True, exist_ok=True)

        # Generate metadata file.
        with (self.bindir / RUBP_METADATA_FILE_NAME).open(
            "w",
            encoding=DEFAULT_CHARSET,
        ) as f:
            f.write(
                json.dumps(
                    self.metadata.to_dict(),
                    indent=2,
                    sort_keys=True,
                ),
            )

        # Get requirements.txt data.
        requirements_txt, path = self.get_requirements_txt()
        dst = self.bindir / RUBP_REQUIREMENTS_FILE_NAME
        if path:
            call_ktrigger(
                IKernelTrigger.on_step,
                msg=fast_format_str(
                    _("Generating requirements.txt from ${{path}} ..."),
                    fmt={"path": make_pretty(path)},
                ),
            )
        if requirements_txt:
            with dst.open(
                "w",
                encoding=DEFAULT_CHARSET,
            ) as f:
                f.write(requirements_txt)

        # Get readme data.
        readme, path = self.get_readme()
        dst = self.bindir / RUBP_README_FILE_NAME
        if path:
            call_ktrigger(IKernelTrigger.on_copy, src=path, dst=dst)
        if readme:
            with dst.open(
                "w",
                encoding=DEFAULT_CHARSET,
            ) as f:
                f.write(readme)

        # Get license data.
        license_, path = self.get_license()
        dst = self.bindir / RUBP_LICENSE_FILE_NAME
        if path:
            call_ktrigger(IKernelTrigger.on_copy, src=path, dst=dst)
        if license_:
            with dst.open(
                "w",
                encoding=DEFAULT_CHARSET,
            ) as f:
                f.write(license_)

        # Compress.
        compress(
            self.bindir,
            self.distdir / f"{self.metadata.name}-{self.version}.rubp",
            start=self.bindir,
            compress_type="zip",
            compress_level=9,
            overwrite=True,
            cwd=self.config.path.parent,
        )
