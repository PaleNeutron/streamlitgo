# Streamlit GO

Package for loading a script before streamlit server start

This package will load `stgo.py` in current working directory before the streamlit server starts. You can use this to patch the streamlit server or to load some data before the server starts!

For example:

- add some code before each page run
- add a custom endpoint to the streamlit server
- get current authenticated user info by custom header

## Installation

```bash
pip install streamlitgo
```

## Usage

Just create your own `stgo.py` in your working directory and use `streamlitgo` instead of `streamlit` in your command line.

```bash
streamlitgo run your_script.py
```

### Example

This example shows how to log each script rerun with the user email and remote ip.


`stgo.py`:

```python
import signal
import typing as T

import streamlit.runtime.app_session
import streamlit.web.bootstrap
import streamlit.web.server
from streamlit.logger import get_logger
from streamlit.runtime.scriptrunner.script_cache import ScriptCache
from streamlit.runtime.scriptrunner.script_run_context import ScriptRunContext
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
        email = self.request.headers.get("x-auth-request-user", "bob@Alice.com")
        remote_ip = self.request.headers.get("X-Real-IP", "192.168.1.1")
        user = session._user_info
        user["email"] = email
        user["remote_ip"] = remote_ip
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
```

