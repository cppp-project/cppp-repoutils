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

"""RuBP metadata generator."""

import contextlib
import datetime
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, cast

from pygit2.repository import Repository
from rubisco.config import LOG_TIME_FORMAT
from rubisco.kernel.config_loader import RUConfiguration
from rubisco.shared.api.exception import RUValueError
from rubisco.shared.api.l10n import _
from rubisco.shared.api.variable import fast_format_str, format_auto
from tzlocal import get_localzone

if TYPE_CHECKING:
    from pygit2 import Commit, Tag

__all__ = ["VersionMetadata", "load_versions"]

GIT_OBJ_BLOB = 3
GIT_OBJ_COMMIT = 1
GIT_OBJ_TAG = 4
GIT_OBJ_TREE = 2


class InvalidObjectTypeError(RUValueError):
    """Invalid object type error."""


@dataclass
class VersionMetadata:
    """Version metadata."""

    version: str
    date: str

    def to_dict(self) -> dict[str, str]:
        """Convert to dict."""
        return asdict(self)


def _get_tag_time(tag: "Tag") -> int:
    obj = tag.get_object()
    if obj.type == GIT_OBJ_COMMIT:
        return cast("Commit", obj).commit_time
    if obj.type == GIT_OBJ_TAG:
        return _get_tag_time(cast("Tag", obj))
    raise InvalidObjectTypeError


def get_tag_time(repo: Repository, tag_name: str) -> int:
    """Get tag time.

    Args:
        repo (Repository): Git repo.
        tag_name (str): Tag name.

    Raises:
        RUValueError: Tag not found.
        InvalidObjectTypeError: Invalid object type.

    Returns:
        int: Tag time.

    """
    tag_ref = f"refs/tags/{tag_name}"
    try:
        ref = repo.references[tag_ref]
    except KeyError as exc:
        msg = fast_format_str(
            _("Tag '${{tag}}' not found."),
            fmt={"tag": tag_name},
        )
        raise RUValueError(msg) from exc

    obj = repo[ref.target]

    if obj.type == GIT_OBJ_TAG:
        return _get_tag_time(cast("Tag", obj))
    if obj.type == GIT_OBJ_COMMIT:
        return cast("Commit", obj).commit_time
    raise InvalidObjectTypeError


def load_versions(
    project_config: RUConfiguration,
    repo: Repository | None,
) -> list[VersionMetadata]:
    """Load versions from json.

    Args:
        project_config (RUConfiguration): Project config.
        repo (Repository | None): Git repo.

    Returns:
        list[VersionMetadata]: Version metadata.

    """
    if repo is None:
        version_list: set[str] = {
            format_auto(
                project_config.config["version"],
                valtype=str,
            ),
        }
    else:
        version_list: set[str] = set()
        tags_list = (
            [
                ref.split("/")[-1]
                for ref in repo.references
                if ref.startswith(
                    "refs/tags/",
                )
            ]
            if repo
            else []
        )
        tags: dict[str, str] = {}
        for tag_name in tags_list.copy():
            with contextlib.suppress(InvalidObjectTypeError):
                tags[tag_name] = datetime.datetime.fromtimestamp(
                    get_tag_time(repo, tag_name),
                    tz=get_localzone(),
                ).strftime(LOG_TIME_FORMAT)
        version_list.update(tags)

    return [VersionMetadata(version=v, date=d) for v, d in version_list]
