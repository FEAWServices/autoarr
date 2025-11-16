# Copyright (C) 2025 AutoArr Contributors
#
# This file is part of AutoArr.
#
# AutoArr is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# AutoArr is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Rate limiting configuration and utilities.

This module provides rate limiting functionality using slowapi,
with configurable limits per endpoint type.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

from .config import get_settings

# Get settings
_settings = get_settings()

# Initialize rate limiter singleton
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[_settings.rate_limit_default],
    enabled=_settings.rate_limit_enabled,
    storage_uri=(
        _settings.redis_url
        if _settings.rate_limit_storage == "redis" and _settings.redis_url
        else "memory://"
    ),
)
