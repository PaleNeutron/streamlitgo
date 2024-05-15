import typing as T

import streamlit.runtime.app_session
import streamlit.web.bootstrap
import streamlit.web.server
from streamlit.logger import get_logger
from streamlit.runtime.scriptrunner.script_cache import ScriptCache
from streamlit.user_info import _get_user_info
from streamlit.web.server import Server
from streamlit.web.server.browser_websocket_handler import BrowserWebSocketHandler

logger = get_logger(__name__)


class MyScriptCache(ScriptCache):
    def get_bytecode(self, script_path: str) -> T.Any:
        user = _get_user_info()
        email = user.get("email", "")
        remote_ip = user.get("remote_ip", "")
        logger.info(f"{email} [{remote_ip}] access script {script_path}")
        return super().get_bytecode(script_path)


streamlit.runtime.runtime.ScriptCache = MyScriptCache


class MyBrowserWebSocketHandler(BrowserWebSocketHandler):
    def open(self, *args, **kwargs) -> T.Awaitable[None] | None:
        ret = super().open(*args, **kwargs)
        session = self._runtime._session_mgr.get_session_info(self._session_id).session
        email = self.request.headers.get("x-auth-request-email", "bob@Alice.com")
        remote_ip = self.request.headers.get("X-Forwarded-For", "192.168.1.1")
        all_headers = list(self.request.headers.get_all())
        # script_path = "streamlitgo/__main__.py"
        # logger.error(f"{email} [{ip}] access script {script_path}")
        user = session._user_info
        user["email"] = email
        user["ip"] = remote_ip.split(",")[0].strip()
        user["all_headers"] = all_headers
        return ret


class StreamlitServer(Server):

    def _create_app(self):
        app = super()._create_app()
        rules = app.wildcard_router.rules
        for rule in rules:
            if issubclass(rule.target, BrowserWebSocketHandler):
                rule.target = MyBrowserWebSocketHandler
                break
        return app


streamlit.web.bootstrap.Server = StreamlitServer
