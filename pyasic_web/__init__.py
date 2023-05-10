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

from fastapi import FastAPI, Security
from pyasic_web import api
from pyasic_web.api.realtime import MinerDataManager
from pyasic_web import auth, errors, routes, settings
from fastapi.staticfiles import StaticFiles
import asyncio

from pyasic_web.auth import AUTH_SCHEME

app = FastAPI(
    exception_handlers=errors.exception_handlers,
    debug=True,
    docs_url=None,
    redoc_url=None
)
app.include_router(routes.router)

static = StaticFiles(directory=settings.STATIC_DIR)
app.mount("/static", static, name="static")

# add API
app.mount("/api", api.app)

@app.on_event("startup")
async def app_startup():
    asyncio.create_task(api.realtime.MinerDataManager().run())
