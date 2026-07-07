import typing as T

import streamlit.runtime.app_session
import streamlit.web.bootstrap
import streamlit.web.server
from streamlit.logger import get_logger
from streamlit.runtime.scriptrunner.script_cache import ScriptCache
from streamlit.user_info import _get_user_info

logger = get_logger(__name__)


class MyScriptCache(ScriptCache):
    def get_bytecode(self, script_path: str) -> T.Any:
        user = _get_user_info()
        email = user.get("email", "")
        remote_ip = user.get("ip", "")
        logger.info(f"{email} [{remote_ip}] access script {script_path}")
        return super().get_bytecode(script_path)


streamlit.runtime.runtime.ScriptCache = MyScriptCache

# Streamlit >= 1.44 replaced the Tornado-based BrowserWebSocketHandler with a
# Starlette/ASGI server.  The old monkey-patch on BrowserWebSocketHandler.open
# no longer works.  Instead we patch _gather_user_info, which is the function
# the new Starlette websocket endpoint calls to extract user info from request
# headers.
#
# For older Streamlit versions (< 1.44) we keep the original
# BrowserWebSocketHandler monkey-patch so the library stays backward-compatible.
try:
    from streamlit.web.server.browser_websocket_handler import (
        BrowserWebSocketHandler,
    )

    origin_open = BrowserWebSocketHandler.open

    def open(self, *args, **kwargs) -> T.Awaitable[None] | None:
        ret = origin_open(self, *args, **kwargs)
        session = (
            self._runtime._session_mgr.get_session_info(self._session_id).session
        )
        email = self.request.headers.get("x-auth-request-email", "bob@Alice.com")
        remote_ip = self.request.headers.get("X-Forwarded-For", "192.168.1.1")
        preferred_username = (
            self.request.headers.get("x-auth-request-preferred-username", "Bob")
            .encode("ISO-8859-1")
            .decode()
        )
        name = (
            self.request.headers.get("x-auth-request-user", "Bob")
            .encode("ISO-8859-1")
            .decode()
        )
        user = session._user_info
        user["name"] = name
        user["preferred_username"] = preferred_username
        user["email"] = email
        user["ip"] = remote_ip.split(",")[0].strip()
        return ret

    BrowserWebSocketHandler.open = open

except ModuleNotFoundError:
    # Streamlit >= 1.44 – Starlette-based server
    import streamlit.web.server.starlette.starlette_websocket as _sw

    _original_gather_user_info = _sw._gather_user_info

    def _gather_user_info(headers) -> dict:
        """Patch _gather_user_info to extract user info from reverse-proxy headers."""
        user_info = _original_gather_user_info(headers)

        email = headers.get("x-auth-request-email", "bob@Alice.com")
        user_info["email"] = email

        remote_ip = headers.get("X-Forwarded-For", "192.168.1.1")
        user_info["ip"] = remote_ip.split(",")[0].strip()

        preferred_username = headers.get("x-auth-request-preferred-username", "Bob")
        user_info["preferred_username"] = (
            preferred_username.encode("ISO-8859-1").decode()
        )

        name = headers.get("x-auth-request-user", "Bob")
        user_info["name"] = name.encode("ISO-8859-1").decode()

        return user_info

    _sw._gather_user_info = _gather_user_info
