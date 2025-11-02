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

"""Test rubisco.lib.speedtest module."""

import asyncio
import sys
from http import HTTPStatus

import pytest
from aiohttp import ClientError, ClientSession, ClientTimeout

from rubisco.lib.speedtest import url_speedtest

TIMEOUT = 5


async def _is_network_reachable() -> bool:
    try:
        async with (
            ClientSession(trust_env=True) as session,
            session.get(
                "http://example.com",
                timeout=ClientTimeout(total=TIMEOUT),
            ) as resp,
        ):
            return resp.status == HTTPStatus.OK
    except (ClientError, OSError):
        return False


def is_network_reachable() -> bool:
    """Check for the network is reachable.

    Returns:
        bool: Return True if network is reachable. False otherwise.

    """
    try:
        return asyncio.run(_is_network_reachable())
    except OSError:
        return False


def test_speedtest() -> None:
    """Test the speedtest module."""
    if not is_network_reachable():
        pytest.skip("Network is unreachable.")
    speed = asyncio.run(url_speedtest("https://example.com"))
    sys.stdout.write(f"Speed of https://example.com: {speed} us.\n")
