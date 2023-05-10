# ------------------------------------------------------------------------------
#  Copyright 2022 Upstream Data Inc                                            -
#                                                                              -
#  Licensed under the Apache License, Version 2.0 (the "License");             -
#  you may not use this file except in compliance with the License.            -
#  You may obtain a copy of the License at                                     -
#                                                                              -
#      http://www.apache.org/licenses/LICENSE-2.0                              -
#                                                                              -
#  Unless required by applicable law or agreed to in writing, software         -
#  distributed under the License is distributed on an "AS IS" BASIS,           -
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.    -
#  See the License for the specific language governing permissions and         -
#  limitations under the License.                                              -
# ------------------------------------------------------------------------------

import ipaddress
import os
from typing import Annotated, Union

import aiofiles
from fastapi import Depends, HTTPException
from fastapi.security import SecurityScopes
from jose import jwt, JWTError
from pydantic import ValidationError
from starlette.requests import Request
from fastapi.websockets import WebSocket

from pyasic import MinerNetwork
from pyasic_web import settings
from pyasic_web.api.auth import ALGORITHM, TokenData
from pyasic_web.auth import user_provider, AUTH_SCHEME, SECRET, User


async def get_current_miner_list(allowed_ips: str = "*"):
    if not allowed_ips:
        return []
    cur_miners = []
    if os.path.exists(settings.MINER_LIST):
        async with aiofiles.open(settings.MINER_LIST) as file:
            async for line in file:
                cur_miners.append(line.strip())
    if not allowed_ips == "*":
        network = MinerNetwork(allowed_ips)
        cur_miners = [
            ip for ip in cur_miners if ipaddress.ip_address(ip) in network.hosts()
        ]
    cur_miners = sorted(cur_miners, key=lambda x: ipaddress.ip_address(x))
    return cur_miners


async def get_user_ip_range(user: User) -> str:
    return user.ip_range


async def get_api_ip_range(user: User) -> str:
    return user.ip_range

async def get_current_user(security_scopes: SecurityScopes, token: Annotated[str, Depends(AUTH_SCHEME)]):
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
    )
    try:
        payload = jwt.decode(token, SECRET, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_scopes = payload.get("scopes", [])
        token_data = TokenData(scopes=token_scopes, username=username)
    except (JWTError, ValidationError):
        raise credentials_exception
    user = await user_provider.find_by_username(token_data.username)
    if user is None:
        raise credentials_exception
    for scope in security_scopes.scopes:
        if scope not in token_data.scopes:
            raise HTTPException(
                status_code=401,
                detail="Not enough permissions",
                headers={"WWW-Authenticate": authenticate_value},
            )
    return user



async def get_all_users():
    return user_provider.user_map


def get_available_cards(page):
    directory = os.path.join(settings.TEMPLATES_DIR, "cards", page)
    card_names = [
        str(f).replace(".html", "")
        for f in os.listdir(directory)
        if os.path.isfile(os.path.join(directory, f))
    ]
    return sorted(card_names)
